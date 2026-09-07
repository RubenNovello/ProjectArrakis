"""
Modulo per la lettura e conversione di file dati.
Supporta CSV, Excel (.xlsx), SQLite (.db), JSON, XML, TXT.
Converte tutto in formato CSV per RawGraphs.
"""
import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
import sqlite3


ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.db', '.json', '.xml', '.txt', '.sql'}


def parse_file(file_path: str, original_filename: str) -> Tuple[bool, str, str]:
    """
    Parses a data file and returns (success, csv_data, error_message).
    Converts all formats to CSV string for RawGraphs consumption.
    """
    ext = original_filename.lower().rsplit('.', 1)[-1] if '.' in original_filename else ''

    if ext == 'csv':
        return parse_csv(file_path)
    elif ext in ('xlsx', 'xls'):
        return parse_excel(file_path)
    elif ext == 'db':
        return parse_sqlite(file_path)
    elif ext == 'json':
        return parse_json(file_path)
    elif ext == 'xml':
        return parse_xml(file_path)
    elif ext in ('txt', 'sql'):
        return parse_txt(file_path)
    else:
        return False, "", f"Formato '{ext}' non supportato"


def parse_csv(file_path: str) -> Tuple[bool, str, str]:
    """Parse CSV file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            dialect = csv.Sniffer().sniff(content[:8192])
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(io.StringIO(content), dialect=dialect)
        output = io.StringIO()
        writer = csv.writer(output)

        headers = None
        for i, row in enumerate(reader):
            if i == 0:
                headers = [h.strip() for h in row]
                writer.writerow(headers)
            else:
                writer.writerow([cell.strip() for cell in row])

        return True, output.getvalue(), ""
    except Exception as e:
        return False, "", f"Errore lettura CSV: {str(e)}"


def parse_excel(file_path: str) -> Tuple[bool, str, str]:
    """Parse Excel file (.xlsx)."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active

        output = io.StringIO()
        writer = csv.writer(output)

        for row in ws.iter_rows(values_only=True):
            writer.writerow([str(cell) if cell is not None else '' for cell in row])

        wb.close()
        return True, output.getvalue(), ""
    except ImportError:
        return False, "", "Libreria openpyxl non installata: pip install openpyxl"
    except Exception as e:
        return False, "", f"Errore lettura Excel: {str(e)}"


def parse_sqlite(file_path: str) -> Tuple[bool, str, str]:
    """Parse SQLite database - reads first table."""
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        if not tables:
            conn.close()
            return False, "", "Nessuna tabella trovata nel database"

        table_name = tables[0][0]

        cursor.execute(f"SELECT * FROM {table_name}")
        headers = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)

        conn.close()
        return True, output.getvalue(), ""
    except Exception as e:
        return False, "", f"Errore lettura SQLite: {str(e)}"


def parse_json(file_path: str) -> Tuple[bool, str, str]:
    """Parse JSON file (array of objects or nested structure)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            if not data:
                return False, "", "Array JSON vuoto"

            headers = list(data[0].keys()) if isinstance(data[0], dict) else [f"col_{i}" for i in range(len(data[0]))]

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)

            for item in data:
                if isinstance(item, dict):
                    writer.writerow([str(item.get(h, '')) for h in headers])
                else:
                    writer.writerow([str(item)])

            return True, output.getvalue(), ""

        elif isinstance(data, dict):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["key", "value"])

            def flatten_dict(d, parent_key=''):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}.{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key))
                    elif isinstance(v, list):
                        items.append((new_key, str(v)))
                    else:
                        items.append((new_key, str(v)))
                return items

            for k, v in flatten_dict(data):
                writer.writerow([k, v])

            return True, output.getvalue(), ""

        else:
            return False, "", "Formato JSON non supportato"

    except Exception as e:
        return False, "", f"Errore lettura JSON: {str(e)}"


def parse_xml(file_path: str) -> Tuple[bool, str, str]:
    """Parse XML file."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        def etree_to_dict(element):
            result = {}
            for child in element:
                child_dict = etree_to_dict(child)
                for k, v in child_dict.items():
                    if child.tag not in result:
                        result[child.tag] = []
                    result[child.tag].append(v)

            if not result:
                return {element.tag: element.text.strip() if element.text and element.text.strip() else ''}

            if len(result) == 1 and list(result.values())[0] == ['']:
                return {element.tag: element.text.strip() if element.text and element.text.strip() else ''}

            return {element.tag: result}

        flat_data = []
        for elem in root:
            flat_data.append(etree_to_dict(elem))

        if not flat_data:
            return False, "", "Nessun dato trovato nel file XML"

        all_keys = set()
        for item in flat_data:
            def collect_keys(d):
                for v in d.values():
                    if isinstance(v, dict):
                        collect_keys(v)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                collect_keys(item)
            collect_keys(item)

        headers = []
        def get_all_keys(d, prefix=''):
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    get_all_keys(v, key)
                elif isinstance(v, list):
                    if v and isinstance(v[0], dict):
                        get_all_keys(v[0], key)
                    else:
                        headers.append(key)
                else:
                    headers.append(key)

        get_all_keys(flat_data[0] if flat_data else {})
        headers = list(dict.fromkeys(headers))

        def flatten(d, keys):
            result = []
            for k in keys:
                parts = k.split('.')
                val = d
                for part in parts:
                    if isinstance(val, dict):
                        val = val.get(part, '')
                    elif isinstance(val, list) and val and isinstance(val[0], dict):
                        val = val[0].get(part, '') if len(val) > 0 else ''
                    else:
                        val = ''
                        break
                result.append(str(val) if val is not None else '')
            return result

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for item in flat_data:
            writer.writerow(flatten(item, headers))

        return True, output.getvalue(), ""

    except Exception as e:
        return False, "", f"Errore lettura XML: {str(e)}"


def parse_txt(file_path: str) -> Tuple[bool, str, str]:
    """Parse TXT/CSV-like file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.strip().split('\n')
        if not lines:
            return False, "", "File vuoto"

        if ',' in lines[0]:
            delimiter = ','
        elif ';' in lines[0]:
            delimiter = ';'
        elif '\t' in lines[0]:
            delimiter = '\t'
        else:
            delimiter = ','

        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        output = io.StringIO()
        writer = csv.writer(output)

        for row in reader:
            writer.writerow([cell.strip() for cell in row])

        return True, output.getvalue(), ""
    except Exception as e:
        return False, "", f"Errore lettura TXT: {str(e)}"


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {ext[1:] for ext in ALLOWED_EXTENSIONS}


def get_file_type(filename: str) -> str:
    """Get file type from filename."""
    if '.' not in filename:
        return 'unknown'
    return filename.rsplit('.', 1)[1].lower()
