"""
Modulo di persistenza dati con SQLite3.
Gestisce tutte le operazioni CRUD per Admin, User e Task.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
from config import DATABASE_PATH, ADMIN_USERNAME
from model import User, Admin, Task, Dataset


class Database:
    """Gestisce la connessione e le operazioni con il database SQLite."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self._db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Inizializza le tabelle del database se non esistono."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titolo TEXT NOT NULL,
                    descrizione TEXT,
                    stato TEXT DEFAULT 'todo',
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attachment BLOB,
                    attachment_name TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descrizione TEXT,
                    file_type TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    data_csv TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            conn.commit()

    def _row_to_user(self, row: sqlite3.Row) -> User:
        return User(
            user_id=row['user_id'],
            username=row['username'],
            password_hash=row['password_hash'],
            email=row['email'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def _row_to_admin(self, row: sqlite3.Row) -> Admin:
        return Admin(
            admin_id=row['admin_id'],
            username=row['username'],
            password_hash=row['password_hash'],
            email=row['email'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            task_id=row['task_id'],
            titolo=row['titolo'],
            descrizione=row['descrizione'] or "",
            stato=row['stato'],
            user_id=row['user_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            attachment=row['attachment'],
            attachment_name=row['attachment_name']
        )

    def _row_to_dataset(self, row: sqlite3.Row) -> Dataset:
        return Dataset(
            dataset_id=row['dataset_id'],
            nome=row['nome'],
            descrizione=row['descrizione'] or "",
            file_type=row['file_type'],
            user_id=row['user_id'],
            file_size=row['file_size'] or 0,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    def create_admin(self, username: str, password_hash: str, email: str) -> Optional[Admin]:
        """Crea un nuovo admin."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO admin (username, password_hash, email) VALUES (?, ?, ?)",
                    (username, password_hash, email)
                )
                conn.commit()
                return self.get_admin_by_username(username)
        except sqlite3.IntegrityError:
            return None

    def get_admin_by_username(self, username: str) -> Optional[Admin]:
        """Recupera admin per username."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
            row = cursor.fetchone()
            return self._row_to_admin(row) if row else None

    def get_admin_by_id(self, admin_id: int) -> Optional[Admin]:
        """Recupera admin per ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,))
            row = cursor.fetchone()
            return self._row_to_admin(row) if row else None

    def create_user(self, username: str, password_hash: str, email: str) -> Optional[User]:
        """Crea un nuovo utente."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                    (username, password_hash, email)
                )
                conn.commit()
                return self.get_user_by_username(username)
        except sqlite3.IntegrityError:
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Recupera utente per username."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Recupera utente per ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def get_all_users(self) -> List[User]:
        """Recupera tutti gli utenti."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]

    def delete_user(self, user_id: int) -> bool:
        """Elimina un utente e i suoi task e dataset."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM datasets WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except Exception:
            return False

    def create_task(self, titolo: str, descrizione: str, stato: str,
                    user_id: int, attachment: Optional[bytes] = None,
                    attachment_name: Optional[str] = None) -> Optional[Task]:
        """Crea un nuovo task."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO tasks (titolo, descrizione, stato, user_id, attachment, attachment_name)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (titolo, descrizione, stato, user_id, attachment, attachment_name)
                )
                conn.commit()
                return self.get_task_by_id(cursor.lastrowid)
        except Exception:
            return None

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Recupera task per ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def get_tasks_by_user(self, user_id: int) -> List[Task]:
        """Recupera tutti i task di un utente."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]

    def get_all_tasks(self) -> List[Task]:
        """Recupera tutti i task di tutti gli utenti (per admin)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]

    def get_tasks_by_status(self, user_id: int, stato: str) -> List[Task]:
        """Recupera task di un utente filtrati per stato."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE user_id = ? AND stato = ? ORDER BY created_at DESC",
                (user_id, stato)
            )
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]

    def update_task(self, task_id: int, titolo: Optional[str] = None,
                    descrizione: Optional[str] = None, stato: Optional[str] = None,
                    attachment: Optional[bytes] = None, attachment_name: Optional[str] = None) -> Optional[Task]:
        """Aggiorna un task esistente."""
        task = self.get_task_by_id(task_id)
        if not task:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if titolo is not None:
                updates.append("titolo = ?")
                params.append(titolo)
            if descrizione is not None:
                updates.append("descrizione = ?")
                params.append(descrizione)
            if stato is not None:
                updates.append("stato = ?")
                params.append(stato)
            if attachment is not None:
                updates.append("attachment = ?")
                params.append(attachment)
            if attachment_name is not None:
                updates.append("attachment_name = ?")
                params.append(attachment_name)

            updates.append("updated_at = CURRENT_TIMESTAMP")

            if updates:
                params.append(task_id)
                cursor.execute(
                    f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?",
                    params
                )
                conn.commit()

            return self.get_task_by_id(task_id)

    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Elimina un task (solo se appartiene all'utente)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM tasks WHERE task_id = ? AND user_id = ?",
                    (task_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def search_tasks(self, user_id: int, query: str) -> List[Task]:
        """Cerca task per titolo o descrizione."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute(
                """SELECT * FROM tasks
                   WHERE user_id = ? AND (titolo LIKE ? OR descrizione LIKE ?)
                   ORDER BY created_at DESC""",
                (user_id, search_term, search_term)
            )
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]

    def create_dataset(self, nome: str, descrizione: str, file_type: str,
                       user_id: int, file_size: int, data_csv: str) -> Optional[Dataset]:
        """Crea un nuovo dataset."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO datasets (nome, descrizione, file_type, user_id, file_size, data_csv)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (nome, descrizione, file_type, user_id, file_size, data_csv)
                )
                conn.commit()
                return self.get_dataset_by_id(cursor.lastrowid)
        except Exception:
            return None

    def get_dataset_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Recupera dataset per ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,))
            row = cursor.fetchone()
            return self._row_to_dataset(row) if row else None

    def get_datasets_by_user(self, user_id: int) -> List[Dataset]:
        """Recupera tutti i dataset di un utente."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM datasets WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [self._row_to_dataset(row) for row in rows]

    def get_all_datasets(self) -> List[Dataset]:
        """Recupera tutti i dataset di tutti gli utenti (per admin)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_dataset(row) for row in rows]

    def get_dataset_data(self, dataset_id: int, user_id: int) -> Optional[str]:
        """Recupera i dati CSV di un dataset (verifica permessi)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data_csv FROM datasets WHERE dataset_id = ? AND user_id = ?",
                (dataset_id, user_id)
            )
            row = cursor.fetchone()
            return row['data_csv'] if row else None

    def get_dataset_data_admin(self, dataset_id: int) -> Optional[str]:
        """Recupera i dati CSV di un dataset (per admin, senza verifica user_id)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_csv FROM datasets WHERE dataset_id = ?", (dataset_id,))
            row = cursor.fetchone()
            return row['data_csv'] if row else None

    def update_dataset(self, dataset_id: int, nome: Optional[str] = None,
                       descrizione: Optional[str] = None) -> Optional[Dataset]:
        """Aggiorna metadata di un dataset."""
        dataset = self.get_dataset_by_id(dataset_id)
        if not dataset:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if nome is not None:
                updates.append("nome = ?")
                params.append(nome)
            if descrizione is not None:
                updates.append("descrizione = ?")
                params.append(descrizione)

            updates.append("updated_at = CURRENT_TIMESTAMP")

            if updates:
                params.append(dataset_id)
                cursor.execute(
                    f"UPDATE datasets SET {', '.join(updates)} WHERE dataset_id = ?",
                    params
                )
                conn.commit()

            return self.get_dataset_by_id(dataset_id)

    def delete_dataset(self, dataset_id: int, user_id: int) -> bool:
        """Elimina un dataset (solo se appartiene all'utente)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM datasets WHERE dataset_id = ? AND user_id = ?",
                    (dataset_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def init_admin_if_not_exists(self, username: str, password_hash: str) -> None:
        """Inizializza l'admin di default se non esiste."""
        existing = self.get_admin_by_username(username)
        if not existing:
            self.create_admin(username, password_hash, f"{username}@arrakis.local")


_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Restituisce l'istanza singleton del database."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
