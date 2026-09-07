"""
Modello dati per Progetto Arrakis.
Contiene le classi User, Admin e Task con incapsulamento della logica di dominio.
"""
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List
from config import TASK_STATES


class User:
    """Rappresenta un utente standard del sistema."""

    def __init__(self, user_id: Optional[int], username: str, password_hash: str,
                 email: str, created_at: Optional[datetime] = None):
        self._user_id = user_id
        self._username = username
        self._password_hash = password_hash
        self._email = email
        self._created_at = created_at or datetime.now()
        self._tasks: List[Task] = []

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def email(self) -> str:
        return self._email

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def tasks(self) -> List['Task']:
        return self._tasks

    def add_task(self, task: 'Task') -> None:
        if task.user_id != self._user_id:
            raise ValueError("Task non appartiene a questo utente")
        self._tasks.append(task)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """Genera hash SHA256 della password con salt opzionale."""
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}${pwd_hash}", salt

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verifica la password confrontando con lo hash memorizzato."""
        try:
            salt, pwd_hash = stored_hash.split('$')
            computed = hashlib.sha256((salt + password).encode()).hexdigest()
            return computed == pwd_hash
        except ValueError:
            return False

    def to_dict(self) -> dict:
        return {
            'user_id': self._user_id,
            'username': self._username,
            'email': self._email,
            'created_at': self._created_at.isoformat() if self._created_at else None
        }


class Admin(User):
    """Rappresenta un amministratore con accesso a tutti gli utenti."""

    def __init__(self, admin_id: Optional[int], username: str, password_hash: str,
                 email: str, created_at: Optional[datetime] = None):
        super().__init__(admin_id, username, password_hash, email, created_at)
        self._all_users: List[User] = []

    @property
    def all_users(self) -> List[User]:
        return self._all_users

    def set_all_users(self, users: List[User]) -> None:
        self._all_users = users

    def get_user_tasks(self, user_id: int) -> List['Task']:
        """Restituisce tutti i task di un utente specifico."""
        for user in self._all_users:
            if user.user_id == user_id:
                return user.tasks
        return []

    def get_all_tasks_across_users(self) -> List['Task']:
        """Restituisce tutti i task di tutti gli utenti."""
        all_tasks = []
        for user in self._all_users:
            all_tasks.extend(user.tasks)
        return all_tasks


class Task:
    """Rappresenta un task associato a un utente."""

    def __init__(self, task_id: Optional[int], titolo: str, descrizione: str,
                 stato: str, user_id: int, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None, attachment: Optional[bytes] = None,
                 attachment_name: Optional[str] = None):
        self._task_id = task_id
        self._titolo = titolo
        self._descrizione = descrizione
        self._stato = stato if stato in TASK_STATES else "todo"
        self._user_id = user_id
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._attachment = attachment
        self._attachment_name = attachment_name

    @property
    def task_id(self) -> int:
        return self._task_id

    @property
    def titolo(self) -> str:
        return self._titolo

    @titolo.setter
    def titolo(self, value: str) -> None:
        if not value or len(value.strip()) == 0:
            raise ValueError("Titolo non può essere vuoto")
        self._titolo = value.strip()
        self._updated_at = datetime.now()

    @property
    def descrizione(self) -> str:
        return self._descrizione

    @descrizione.setter
    def descrizione(self, value: str) -> None:
        self._descrizione = value
        self._updated_at = datetime.now()

    @property
    def stato(self) -> str:
        return self._stato

    @stato.setter
    def stato(self, value: str) -> None:
        if value not in TASK_STATES:
            raise ValueError(f"Stato deve essere uno di: {TASK_STATES}")
        self._stato = value
        self._updated_at = datetime.now()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def attachment(self) -> Optional[bytes]:
        return self._attachment

    @attachment.setter
    def attachment(self, value: Optional[bytes]) -> None:
        self._attachment = value
        self._updated_at = datetime.now()

    @property
    def attachment_name(self) -> Optional[str]:
        return self._attachment_name

    @attachment_name.setter
    def attachment_name(self, value: Optional[str]) -> None:
        self._attachment_name = value

    def to_dict(self) -> dict:
        return {
            'task_id': self._task_id,
            'titolo': self._titolo,
            'descrizione': self._descrizione,
            'stato': self._stato,
            'user_id': self._user_id,
            'created_at': self._created_at.isoformat() if self._created_at else None,
            'updated_at': self._updated_at.isoformat() if self._updated_at else None,
            'attachment_name': self._attachment_name
        }

    def __repr__(self) -> str:
        return f"Task(id={self._task_id}, titolo='{self._titolo}', stato='{self._stato}')"


class Dataset:
    """Rappresenta un dataset caricato dall'utente (CSV, Excel, SQLite, ecc.)."""

    def __init__(self, dataset_id: Optional[int], nome: str, descrizione: str,
                 file_type: str, user_id: int, file_size: int,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self._dataset_id = dataset_id
        self._nome = nome
        self._descrizione = descrizione
        self._file_type = file_type
        self._user_id = user_id
        self._file_size = file_size
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    @property
    def dataset_id(self) -> int:
        return self._dataset_id

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, value: str) -> None:
        if not value or len(value.strip()) == 0:
            raise ValueError("Nome non può essere vuoto")
        self._nome = value.strip()
        self._updated_at = datetime.now()

    @property
    def descrizione(self) -> str:
        return self._descrizione

    @descrizione.setter
    def descrizione(self, value: str) -> None:
        self._descrizione = value
        self._updated_at = datetime.now()

    @property
    def file_type(self) -> str:
        return self._file_type

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def file_size(self) -> int:
        return self._file_size

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def to_dict(self) -> dict:
        return {
            'dataset_id': self._dataset_id,
            'nome': self._nome,
            'descrizione': self._descrizione,
            'file_type': self._file_type,
            'user_id': self._user_id,
            'file_size': self._file_size,
            'created_at': self._created_at.isoformat() if self._created_at else None,
            'updated_at': self._updated_at.isoformat() if self._updated_at else None
        }

    def __repr__(self) -> str:
        return f"Dataset(id={self._dataset_id}, nome='{self._nome}', type='{self._file_type}')"
