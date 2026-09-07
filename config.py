"""
Configurazione applicazione Progetto Arrakis.
Contiene tutte le costanti e configurazioni centralizzate.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "arrakis.db")

ADMIN_USERNAME = "progetto_arrakis"
ADMIN_PASSWORD = "shai_hulud_2026"

SESSION_TIMEOUT = 3600

ALLOWED_FILE_EXTENSIONS = {'.csv', '.db', '.xlsx', '.json', '.xml', '.sql', '.txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024

TASK_STATES = ["todo", "in_progress", "done"]

CLI_COLORS = {
    "header": "\033[95m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "end": "\033[0m",
    "bold": "\033[1m"
}
