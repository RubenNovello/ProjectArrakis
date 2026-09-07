"""
Main per Progetto Arrakis.
Punto di ingresso dell'applicazione MVC.
"""
import os
from typing import Optional
from model import User, Admin, Task
from controller import AuthController, UserController, TaskController, AdminTaskController
from view import CLIView
from db import get_database
from config import DATABASE_PATH


class Application:
    """Applicazione principale che orchestra MVC."""

    def __init__(self):
        self._view = CLIView()
        self._current_user: Optional[User] = None
        self._current_admin: Optional[Admin] = None
        self._is_admin = False
        AuthController.init_admin()

    def run(self) -> None:
        """Loop principale dell'applicazione."""
        self._view.show_welcome()

        while True:
            if self._current_user is None and self._current_admin is None:
                self._handle_auth_menu()
            elif self._is_admin:
                self._handle_admin_menu()
            else:
                self._handle_user_menu()

    def _handle_auth_menu(self) -> None:
        choice = self._view.show_login_menu()

        if choice == 1:
            self._login_user()
        elif choice == 2:
            self._register_user()
        elif choice == 3:
            self._login_admin()
        elif choice == 0:
            self._view.show_goodbye()
            return

    def _handle_user_menu(self) -> None:
        choice = self._view.show_user_menu(self._current_user.username)

        if choice == 1:
            self._show_my_tasks()
        elif choice == 2:
            self._create_task()
        elif choice == 3:
            self._edit_task()
        elif choice == 4:
            self._delete_task()
        elif choice == 5:
            self._filter_tasks()
        elif choice == 6:
            self._search_tasks()
        elif choice == 7:
            self._export_data()
        elif choice == 0:
            self._logout()

    def _handle_admin_menu(self) -> None:
        choice = self._view.show_admin_menu(self._current_admin.username)

        if choice == 1:
            self._show_all_tasks()
        elif choice == 2:
            self._show_all_users()
        elif choice == 3:
            self._show_user_tasks_admin()
        elif choice == 4:
            self._edit_task_admin()
        elif choice == 5:
            self._delete_user_admin()
        elif choice == 0:
            self._logout()

    def _login_user(self) -> None:
        username = self._view.get_input("Username")
        password = self._view.get_password("Password")

        success, message, user = AuthController.login_user(username, password)
        if success:
            self._current_user = user
            self._is_admin = False
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _register_user(self) -> None:
        username = self._view.get_input("Username")
        email = self._view.get_input("Email")
        password = self._view.get_password("Password")
        confirm_password = self._view.get_password("Conferma Password")

        if password != confirm_password:
            self._view.print_error("Le password non coincidono")
            self._view.pause()
            return

        success, message = AuthController.register_user(username, password, email)
        if success:
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _login_admin(self) -> None:
        username = self._view.get_input("Username Admin")
        password = self._view.get_password("Password Admin")

        success, message, admin = AuthController.login_admin(username, password)
        if success:
            self._current_admin = admin
            self._is_admin = True
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _logout(self) -> None:
        self._current_user = None
        self._current_admin = None
        self._is_admin = False
        self._view.print_info("Disconnesso con successo")
        self._view.pause()

    def _show_my_tasks(self) -> None:
        if not self._current_user:
            return
        tasks = TaskController.get_user_tasks(self._current_user)
        self._view.show_tasks(tasks, "I tuoi Task")
        self._view.pause()

    def _create_task(self) -> None:
        if not self._current_user:
            return

        task_data = self._view.show_task_form()
        attachment = None
        attachment_name = None

        do_attach = self._view.get_input("Allega file? (s/n)")
        if do_attach.lower() == 's':
            file_path = self._view.show_file_import()
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        attachment = f.read()
                    attachment_name = os.path.basename(file_path)
                except Exception as e:
                    self._view.print_error(f"Errore lettura file: {e}")

        success, message, task = TaskController.create_task(
            task_data['titolo'],
            task_data['descrizione'],
            task_data['stato'],
            self._current_user,
            attachment,
            attachment_name
        )

        if success:
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _edit_task(self) -> None:
        if not self._current_user:
            return

        task_id_str = self._view.get_input("ID Task da modificare")
        try:
            task_id = int(task_id_str)
        except ValueError:
            self._view.print_error("ID non valido")
            self._view.pause()
            return

        task = TaskController.get_task_by_id(task_id, self._current_user)
        if not task:
            self._view.print_error("Task non trovato")
            self._view.pause()
            return

        self._view.show_tasks([task], f"Task #{task_id}")
        print(f"[1] Modifica titolo")
        print(f"[2] Modifica descrizione")
        print(f"[3] Modifica stato")
        print(f"[0] Annulla")

        choice = self._view.get_choice(3)

        if choice == 1:
            new_titolo = self._view.get_input("Nuovo titolo")
            success, message = TaskController.update_task(task_id, self._current_user, titolo=new_titolo)
        elif choice == 2:
            new_desc = self._view.get_input("Nuova descrizione")
            success, message = TaskController.update_task(task_id, self._current_user, descrizione=new_desc)
        elif choice == 3:
            stato = self._view.show_status_filter()
            if stato:
                success, message = TaskController.update_task(task_id, self._current_user, stato=stato)
            else:
                success, message = False, "Stato non valido"
        else:
            return

        if success:
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _delete_task(self) -> None:
        if not self._current_user:
            return

        task_id_str = self._view.get_input("ID Task da eliminare")
        try:
            task_id = int(task_id_str)
        except ValueError:
            self._view.print_error("ID non valido")
            self._view.pause()
            return

        confirm = self._view.get_input("Confermi l'eliminazione? (s/n)")
        if confirm.lower() != 's':
            return

        success, message = TaskController.delete_task(task_id, self._current_user)
        if success:
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _filter_tasks(self) -> None:
        if not self._current_user:
            return

        stato = self._view.show_status_filter()
        if stato:
            tasks = TaskController.get_tasks_by_status(self._current_user, stato)
        else:
            tasks = TaskController.get_user_tasks(self._current_user)

        self._view.show_tasks(tasks, f"Task - Stato: {stato or 'Tutti'}")
        self._view.pause()

    def _search_tasks(self) -> None:
        if not self._current_user:
            return

        query = self._view.get_input("Termine di ricerca")
        if not query:
            self._view.print_error("Inserisci un termine di ricerca")
            self._view.pause()
            return

        tasks = TaskController.search_tasks(self._current_user, query)
        self._view.show_tasks(tasks, f"Risultati per '{query}'")
        self._view.pause()

    def _export_data(self) -> None:
        if not self._current_user:
            return

        self._view.print_info("Funzione di esportazione in sviluppo")
        self._view.pause()

    def _show_all_tasks(self) -> None:
        if not self._current_admin:
            return

        tasks = AdminTaskController.get_all_tasks()
        self._view.show_tasks(tasks, "Tutti i Task")
        self._view.pause()

    def _show_all_users(self) -> None:
        if not self._current_admin:
            return

        users = UserController.get_all_users()
        self._view.show_users(users)
        self._view.pause()

    def _show_user_tasks_admin(self) -> None:
        if not self._current_admin:
            return

        user_id_str = self._view.get_input("ID Utente")
        try:
            user_id = int(user_id_str)
        except ValueError:
            self._view.print_error("ID non valido")
            self._view.pause()
            return

        user = UserController.get_user_by_id(user_id)
        if not user:
            self._view.print_error("Utente non trovato")
            self._view.pause()
            return

        tasks = AdminTaskController.get_user_tasks(user_id)
        self._view.show_tasks(tasks, f"Task di {user.username}")
        self._view.pause()

    def _edit_task_admin(self) -> None:
        if not self._current_admin:
            return

        task_id_str = self._view.get_input("ID Task")
        try:
            task_id = int(task_id_str)
        except ValueError:
            self._view.print_error("ID non valido")
            self._view.pause()
            return

        stato = self._view.show_status_filter()
        if not stato:
            self._view.pause()
            return

        success, message = AdminTaskController.update_task_status(task_id, stato, self._current_admin)
        if success:
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()

    def _delete_user_admin(self) -> None:
        if not self._current_admin:
            return

        user_id_str = self._view.get_input("ID Utente da eliminare")
        try:
            user_id = int(user_id_str)
        except ValueError:
            self._view.print_error("ID non valido")
            self._view.pause()
            return

        confirm = self._view.get_input("Confermi l'eliminazione dell'utente e tutti i suoi task? (s/n)")
        if confirm.lower() != 's':
            return

        success, message = UserController.delete_user(user_id, self._current_admin)
        if success:
            self._view.print_success(message)
        else:
            self._view.print_error(message)
        self._view.pause()


def main():
    """Entry point dell'applicazione."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
