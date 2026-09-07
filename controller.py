"""
Controller per Progetto Arrakis.
Gestisce la logica di business per utenti, admin e task.
"""
import os
from typing import Optional, List, Tuple
from model import User, Admin, Task, Dataset
from db import get_database
from config import ADMIN_USERNAME, ADMIN_PASSWORD, TASK_STATES
from data_parser import parse_file, is_allowed_file, get_file_type
import config


class AuthController:
    """Gestisce autenticazione e registrazione."""

    @staticmethod
    def register_user(username: str, password: str, email: str) -> Tuple[bool, str]:
        """Registra un nuovo utente."""
        if not username or len(username) < 3:
            return False, "Username deve essere almeno 3 caratteri"
        if not password or len(password) < 6:
            return False, "Password deve essere almeno 6 caratteri"
        if not email or '@' not in email:
            return False, "Email non valida"

        db = get_database()
        existing = db.get_user_by_username(username)
        if existing:
            return False, "Username già esistente"

        password_hash, _ = User.hash_password(password)
        user = db.create_user(username, password_hash, email)

        if user:
            return True, f"Utente {username} registrato con successo"
        return False, "Errore durante la registrazione"

    @staticmethod
    def login_user(username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Autentica un utente."""
        db = get_database()
        user = db.get_user_by_username(username)

        if not user:
            return False, "Username non trovato", None

        if not User.verify_password(password, user.password_hash):
            return False, "Password errata", None

        return True, f"Benvenuto {username}", user

    @staticmethod
    def login_admin(username: str, password: str) -> Tuple[bool, str, Optional[Admin]]:
        """Autentica un admin."""
        db = get_database()
        admin = db.get_admin_by_username(username)

        if not admin:
            return False, "Admin non trovato", None

        if not User.verify_password(password, admin.password_hash):
            return False, "Password errata", None

        return True, f"Benvenuto Admin {username}", admin

    @staticmethod
    def init_admin() -> None:
        """Inizializza l'admin di default."""
        db = get_database()
        password_hash, _ = Admin.hash_password(ADMIN_PASSWORD)
        db.init_admin_if_not_exists(ADMIN_USERNAME, password_hash)


class UserController:
    """Gestisce le operazioni sugli utenti (solo per admin)."""

    @staticmethod
    def get_all_users() -> List[User]:
        """Restituisce tutti gli utenti."""
        db = get_database()
        return db.get_all_users()

    @staticmethod
    def delete_user(user_id: int, admin: Admin) -> Tuple[bool, str]:
        """Elimina un utente (solo admin)."""
        db = get_database()
        user = db.get_user_by_id(user_id)
        if not user:
            return False, "Utente non trovato"

        if db.delete_user(user_id):
            return True, f"Utente {user.username} eliminato"
        return False, "Errore durante l'eliminazione"

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Restituisce un utente per ID."""
        db = get_database()
        return db.get_user_by_id(user_id)


class TaskController:
    """Gestisce le operazioni sui task."""

    @staticmethod
    def create_task(titolo: str, descrizione: str, stato: str,
                    user: User, attachment: Optional[bytes] = None,
                    attachment_name: Optional[str] = None) -> Tuple[bool, str, Optional[Task]]:
        """Crea un nuovo task per l'utente."""
        if not titolo or len(titolo.strip()) == 0:
            return False, "Titolo non può essere vuoto", None

        if stato not in TASK_STATES:
            return False, f"Stato deve essere uno di: {', '.join(TASK_STATES)}", None

        db = get_database()
        task = db.create_task(titolo.strip(), descrizione, stato, user.user_id,
                             attachment, attachment_name)

        if task:
            return True, "Task creato con successo", task
        return False, "Errore durante la creazione del task", None

    @staticmethod
    def get_user_tasks(user: User) -> List[Task]:
        """Restituisce tutti i task dell'utente."""
        db = get_database()
        return db.get_tasks_by_user(user.user_id)

    @staticmethod
    def get_tasks_by_status(user: User, stato: str) -> List[Task]:
        """Restituisce i task filtrati per stato."""
        if stato not in TASK_STATES:
            return []
        db = get_database()
        return db.get_tasks_by_status(user.user_id, stato)

    @staticmethod
    def update_task(task_id: int, user: User, titolo: Optional[str] = None,
                    descrizione: Optional[str] = None, stato: Optional[str] = None,
                    attachment: Optional[bytes] = None, attachment_name: Optional[str] = None) -> Tuple[bool, str]:
        """Aggiorna un task esistente."""
        db = get_database()
        existing = db.get_task_by_id(task_id)

        if not existing:
            return False, "Task non trovato"

        if existing.user_id != user.user_id:
            return False, "Non hai permesso di modificare questo task"

        if stato and stato not in TASK_STATES:
            return False, f"Stato deve essere uno di: {', '.join(TASK_STATES)}"

        updated = db.update_task(task_id, titolo, descrizione, stato, attachment, attachment_name)

        if updated:
            return True, "Task aggiornato con successo"
        return False, "Errore durante l'aggiornamento"

    @staticmethod
    def delete_task(task_id: int, user: User) -> Tuple[bool, str]:
        """Elimina un task."""
        db = get_database()
        existing = db.get_task_by_id(task_id)

        if not existing:
            return False, "Task non trovato"

        if existing.user_id != user.user_id:
            return False, "Non hai permesso di eliminare questo task"

        if db.delete_task(task_id, user.user_id):
            return True, "Task eliminato con successo"
        return False, "Errore durante l'eliminazione"

    @staticmethod
    def search_tasks(user: User, query: str) -> List[Task]:
        """Cerca task per titolo o descrizione."""
        db = get_database()
        return db.search_tasks(user.user_id, query)

    @staticmethod
    def get_task_by_id(task_id: int, user: User) -> Optional[Task]:
        """Restituisce un task per ID (solo se appartiene all'utente)."""
        db = get_database()
        task = db.get_task_by_id(task_id)
        if task and task.user_id == user.user_id:
            return task
        return None


class AdminTaskController:
    """Gestisce i task per l'admin (accesso a tutti i task)."""

    @staticmethod
    def get_all_tasks() -> List[Task]:
        """Restituisce tutti i task di tutti gli utenti."""
        db = get_database()
        return db.get_all_tasks()

    @staticmethod
    def get_user_tasks(user_id: int) -> List[Task]:
        """Restituisce tutti i task di un utente specifico."""
        db = get_database()
        return db.get_tasks_by_user(user_id)

    @staticmethod
    def update_task_status(task_id: int, stato: str, admin: Admin) -> Tuple[bool, str]:
        """Aggiorna lo stato di un task (admin)."""
        if stato not in TASK_STATES:
            return False, f"Stato deve essere uno di: {', '.join(TASK_STATES)}"

        db = get_database()
        task = db.get_task_by_id(task_id)

        if not task:
            return False, "Task non trovato"

        updated = db.update_task(task_id, stato=stato)

        if updated:
            return True, f"Stato task aggiornato a '{stato}'"
        return False, "Errore durante l'aggiornamento"


class DatasetController:
    """Gestisce le operazioni sui dataset."""

    @staticmethod
    def upload_dataset(file_path: str, filename: str, nome: str,
                       descrizione: str, user: User) -> Tuple[bool, str, Optional[Dataset]]:
        """Carica e salva un dataset per l'utente."""
        if not is_allowed_file(filename):
            return False, f"Formato file non supportato. Formati: CSV, XLSX, DB, JSON, XML, SQL, TXT", None

        success, csv_data, error = parse_file(file_path, filename)

        if not success:
            return False, error, None

        if not csv_data or len(csv_data.strip()) == 0:
            return False, "Il file non contiene dati validi", None

        db = get_database()
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else len(csv_data)
        file_type = get_file_type(filename)

        dataset = db.create_dataset(
            nome=nome,
            descrizione=descrizione,
            file_type=file_type,
            user_id=user.user_id,
            file_size=file_size,
            data_csv=csv_data
        )

        if dataset:
            return True, "Dataset caricato con successo", dataset
        return False, "Errore durante il salvataggio del dataset", None

    @staticmethod
    def get_user_datasets(user: User) -> List[Dataset]:
        """Restituisce tutti i dataset dell'utente."""
        db = get_database()
        return db.get_datasets_by_user(user.user_id)

    @staticmethod
    def get_dataset_data(dataset_id: int, user: User) -> Tuple[bool, str, str]:
        """Recupera i dati di un dataset (verifica permessi)."""
        db = get_database()
        data = db.get_dataset_data(dataset_id, user.user_id)
        if data is None:
            return False, "", "Dataset non trovato o non autorizzato"
        return True, data, ""

    @staticmethod
    def delete_dataset(dataset_id: int, user: User) -> Tuple[bool, str]:
        """Elimina un dataset."""
        db = get_database()
        existing = db.get_dataset_by_id(dataset_id)

        if not existing:
            return False, "Dataset non trovato"

        if existing.user_id != user.user_id:
            return False, "Non hai permesso di eliminare questo dataset"

        if db.delete_dataset(dataset_id, user.user_id):
            return True, "Dataset eliminato con successo"
        return False, "Errore durante l'eliminazione"

    @staticmethod
    def update_dataset(dataset_id: int, user: User, nome: Optional[str] = None,
                      descrizione: Optional[str] = None) -> Tuple[bool, str]:
        """Aggiorna metadata di un dataset."""
        db = get_database()
        existing = db.get_dataset_by_id(dataset_id)

        if not existing:
            return False, "Dataset non trovato"

        if existing.user_id != user.user_id:
            return False, "Non hai permesso di modificare questo dataset"

        updated = db.update_dataset(dataset_id, nome, descrizione)

        if updated:
            return True, "Dataset aggiornato con successo"
        return False, "Errore durante l'aggiornamento"

    @staticmethod
    def get_dataset_by_id(dataset_id: int, user: User) -> Optional[Dataset]:
        """Restituisce un dataset per ID (solo se appartiene all'utente)."""
        db = get_database()
        dataset = db.get_dataset_by_id(dataset_id)
        if dataset and dataset.user_id == user.user_id:
            return dataset
        return None


class AdminDatasetController:
    """Gestisce i dataset per l'admin (accesso a tutti i dataset)."""

    @staticmethod
    def get_all_datasets() -> List[Dataset]:
        """Restituisce tutti i dataset di tutti gli utenti."""
        db = get_database()
        return db.get_all_datasets()

    @staticmethod
    def get_user_datasets(user_id: int) -> List[Dataset]:
        """Restituisce tutti i dataset di un utente specifico."""
        db = get_database()
        return db.get_datasets_by_user(user_id)

    @staticmethod
    def get_dataset_data_admin(dataset_id: int) -> Tuple[bool, str, str]:
        """Recupera i dati di un dataset (per admin)."""
        db = get_database()
        data = db.get_dataset_data_admin(dataset_id)
        if data is None:
            return False, "", "Dataset non trovato"
        return True, data, ""

    @staticmethod
    def get_dataset_by_id(dataset_id: int) -> Optional[Dataset]:
        """Restituisce un dataset per ID."""
        db = get_database()
        return db.get_dataset_by_id(dataset_id)
