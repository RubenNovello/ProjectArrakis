"""
View per Progetto Arrakis - Interfaccia CLI.
Gestisce tutta l'interazione con l'utente in modalità testuale.
"""
import os
import sys
from typing import Optional, List
from model import User, Admin, Task
from config import CLI_COLORS, TASK_STATES, ALLOWED_FILE_EXTENSIONS


class CLIView:
    """Interfaccia a riga di comando per l'applicazione."""

    def __init__(self):
        self._colors = CLI_COLORS

    def _color(self, color: str, text: str) -> str:
        return f"{self._colors.get(color, '')}{text}{self._colors['end']}"

    def _bold(self, text: str) -> str:
        return f"{self._colors['bold']}{text}{self._colors['end']}"

    def clear_screen(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str) -> None:
        print(f"\n{self._color('header', '=' * 60)}")
        print(f"{self._color('header', self._bold(f'  {title}'))}")
        print(f"{self._color('header', '=' * 60)}\n")

    def print_success(self, message: str) -> None:
        print(f"{self._color('green', '[OK]')} {message}")

    def print_error(self, message: str) -> None:
        print(f"{self._color('red', '[ERRORE]')} {message}")

    def print_warning(self, message: str) -> None:
        print(f"{self._color('yellow', '[AVVISO]')} {message}")

    def print_info(self, message: str) -> None:
        print(f"{self._color('cyan', '[INFO]')} {message}")

    def print_menu(self, options: List[str]) -> None:
        for i, option in enumerate(options, 1):
            print(f"  {self._color('cyan', f'{i}.')} {option}")
        print()

    def get_input(self, prompt: str) -> str:
        return input(f"{self._color('yellow', prompt)}: ").strip()

    def get_password(self, prompt: str) -> str:
        return input(f"{self._color('yellow', prompt)}: ").strip()

    def get_choice(self, max_options: int) -> Optional[int]:
        try:
            choice = input(f"{self._color('yellow', 'Scelta')} (1-{max_options}): ").strip()
            if not choice:
                return None
            choice_int = int(choice)
            if 1 <= choice_int <= max_options:
                return choice_int
            return None
        except ValueError:
            return None

    def show_welcome(self) -> None:
        self.clear_screen()
        print(f"\n{self._color('header', '╔══════════════════════════════════════════════════════════╗')}")
        print(f"{self._color('header', '║')}  {self._bold('PROGETTO ARRAKIS - Dashboard tipo Tableau')}{' ' * 20}{self._color('header', '║')}")
        print(f"{self._color('header', '║')}  {self._color('yellow', 'Il Deserto ti chiama. I Task ti aspettano.')}{' ' * 18}{self._color('header', '║')}")
        print(f"{self._color('header', '╚══════════════════════════════════════════════════════════╝')}\n")

    def show_login_menu(self) -> int:
        print(f"  {self._color('cyan', '1.')} Login Utente")
        print(f"  {self._color('cyan', '2.')} Registrazione")
        print(f"  {self._color('cyan', '3.')} Login Admin")
        print(f"  {self._color('red', '0.')} Esci\n")
        return self.get_choice(3) or 0

    def show_user_menu(self, username: str) -> int:
        print(f"\n{self._color('green', 'Utente loggato:')} {self._bold(username)}")
        print(f"{self._color('header', '-' * 50)}")
        print(f"  {self._color('cyan', '1.')} Mostra i miei Task")
        print(f"  {self._color('cyan', '2.')} Crea nuovo Task")
        print(f"  {self._color('cyan', '3.')} Modifica Task")
        print(f"  {self._color('cyan', '4.')} Elimina Task")
        print(f"  {self._color('cyan', '5.')} Filtra per stato")
        print(f"  {self._color('cyan', '6.')} Cerca Task")
        print(f"  {self._color('cyan', '7.')} Esporta dati")
        print(f"  {self._color('red', '0.')} Logout\n")
        return self.get_choice(7) or 0

    def show_admin_menu(self, username: str) -> int:
        print(f"\n{self._color('yellow', 'Admin loggato:')} {self._bold(username)}")
        print(f"{self._color('header', '-' * 50)}")
        print(f"  {self._color('cyan', '1.')} Mostra tutti i Task")
        print(f"  {self._color('cyan', '2.')} Mostra tutti gli Utenti")
        print(f"  {self._color('cyan', '3.')} Task di un Utente")
        print(f"  {self._color('cyan', '4.')} Modifica stato Task")
        print(f"  {self._color('cyan', '5.')} Elimina Utente")
        print(f"  {self._color('red', '0.')} Logout\n")
        return self.get_choice(5) or 0

    def show_tasks(self, tasks: List[Task], title: str = "Task") -> None:
        if not tasks:
            self.print_warning("Nessun task trovato")
            return

        print(f"\n{self._color('header', f'╔═══ {title} ({len(tasks)}) ═══╗')}")
        for task in tasks:
            stato_color = 'green' if task.stato == 'done' else ('yellow' if task.stato == 'in_progress' else 'cyan')
            print(f"{self._color('header', '║')}")
            print(f"{self._color('header', '║')}  {self._bold(f'#{task.task_id}')} - {task.titolo}")
            print(f"{self._color('header', '║')}     {task.descrizione[:60]}...")
            print(f"{self._color('header', '║')}     Stato: {self._color(stato_color, task.stato.upper())}")
            if task.attachment_name:
                print(f"{self._color('header', '║')}     Allegato: {task.attachment_name}")
            print(f"{self._color('header', '║')}     Creato: {task.created_at.strftime('%d/%m/%Y %H:%M')}")
        print(f"{self._color('header', '╚' + '═' * 39 + '╝')}\n")

    def show_users(self, users: List[User]) -> None:
        if not users:
            self.print_warning("Nessun utente trovato")
            return

        print(f"\n{self._color('yellow', '╔═══ Utenti Registrati ═══╗')}")
        for user in users:
            print(f"{self._color('yellow', '║')}  {self._bold(f'#{user.user_id}')} - {user.username} ({user.email})")
        print(f"{self._color('yellow', '╚' + '═' * 24 + '╝')}\n")

    def show_task_form(self) -> dict:
        titolo = self.get_input("Titolo task")
        descrizione = self.get_input("Descrizione")
        print(f"\nStati disponibili: {', '.join(TASK_STATES)}")
        stato = self.get_input(f"Stato (default: todo)")
        if not stato:
            stato = "todo"
        return {'titolo': titolo, 'descrizione': descrizione, 'stato': stato}

    def show_status_filter(self) -> Optional[str]:
        print(f"\nStati disponibili: {', '.join(TASK_STATES)}")
        stato = self.get_input("Filtra per stato (invio per tutti)")
        if stato in TASK_STATES:
            return stato
        return None

    def show_billboard(self, tasks: List[Task]) -> None:
        self.clear_screen()
        print(f"\n{self._color('yellow', '╔═══════════════════════════════════════════════════════════╗')}")
        print(f"{self._color('yellow', '║')}        {self._bold('BACHECA TASK - PROGETTO ARRAKIS')}{' ' * 19}{self._color('yellow', '║')}")
        print(f"{self._color('yellow', '╚═══════════════════════════════════════════════════════════╝')}\n")

        todo = [t for t in tasks if t.stato == 'todo']
        in_progress = [t for t in tasks if t.stato == 'in_progress']
        done = [t for t in tasks if t.stato == 'done']

        self._print_column("TODO", todo, 'cyan')
        self._print_column("IN PROGRESS", in_progress, 'yellow')
        self._print_column("DONE", done, 'green')

    def _print_column(self, title: str, tasks: List[Task], color: str) -> None:
        print(f"{self._color(color, '┌─ ' + title + ' ─' * 20)}")
        if not tasks:
            print(f"{self._color(color, '│')}  (vuoto)")
        else:
            for task in tasks[:5]:
                print(f"{self._color(color, '│')}  {task.titolo[:25]}")
                if len(task.titolo) > 25:
                    print(f"{self._color(color, '│')}    {task.titolo[25:50]}")
        print(f"{self._color(color, '└' + '─' * 25)}\n")

    def show_file_import(self) -> Optional[str]:
        print(f"\nFormati supportati: {', '.join(ALLOWED_FILE_EXTENSIONS)}")
        path = self.get_input("Percorso file da importare")
        if path and os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in ALLOWED_FILE_EXTENSIONS:
                return path
            else:
                self.print_error(f"Formato {ext} non supportato")
        else:
            self.print_error("File non trovato")
        return None

    def pause(self) -> None:
        input(f"\n{self._color('yellow', 'Premi INVIO per continuare...')}")

    def show_goodbye(self) -> None:
        self.clear_screen()
        print(f"\n{self._color('header', '╔══════════════════════════════════════════════════════════╗')}")
        print(f"{self._color('header', '║')}  {self._color('yellow', 'Arrivederci! Il Deserto ti ricorderà.')}{' ' * 21}{self._color('header', '║')}")
        print(f"{self._color('header', '╚══════════════════════════════════════════════════════════╝')}\n")
