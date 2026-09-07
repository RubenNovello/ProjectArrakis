# Titolo del progetto: 'Progetto Arrakis – Applicativo tabellare in python Open Source'
## 🧩 Descrizione Generale
    Costruisci un'applicazione Python, organizzata secondo il paradigma MVC, per gestire un front-end tabellare.L'applicazione permette a ciascun utente di registrarsi, accedere con login, aggiungere e gestire i propri dati (provenienti da .csv, .db., .xlsx, .csv, .json, .xml, .sql, .txt).

## 🟢 Step 1 – Setup progetto e struttura MVC
    • Crea la struttura base del progetto con i file: model.py, view.py, controller.py, main.py.
    • Applica il pattern MVC con moduli separati.
    • Aggiungi un breve commento esplicativo della struttura.

## 🟡 Step 2 – Classi e OOP
    • Progetta le classi ADMIN, USER e Task con metodi e attributi appropriati.
        • Admin può accedere ai dati di ogni singolo user, e vedere i relativi task di ogni singolo user.
        • User può accedere solo ai propri dati.
    • Incapsula la logica di dominio (costruttori, metodi, proprietà ).
    • I Task devono avere: id, titolo, descrizione, stato, utente assegnato.

## 🔵 Step 3 – Persistenza dati con SQLite3
    • Crea un database SQLite con le tabelle Admin, User e Task.
    • Implementa le operazioni CRUD.
    • Organizza la logica database in un modulo separato (es. db.py).
    - Crea una sezione BLOB (Binary Language Object) per salvare eventuali file allegati ai task dei singoli utenti
    - ogni utente può vedere esclusivamente i propri task e non quelli degli altri utenti, con i propri task
        🧿 Step 3b – Registrazione e Login Utente
        • Implementa registrazione e login con username e password hashata.
        • Usa hashlib.sha256 per l’hashing della password.
        • Dopo il login, l’utente può accedere solo ai propri task.

## 🟠 Step 4 – Costruzione del controller
    • Il controller gestisce l’aggiunta utenti, creazione task, aggiornamento stato, filtro per utente e stato.
    • Tutte le operazioni sono limitate all’utente autenticato.

## 🔴 Step 5 – View a riga di comando
    • Realizza una CLI leggibile e interattiva.
    • Visualizza task, errori, messaggi di conferma.
    • Usa input/output puliti.

## ⚫ Step 6 – Modularizzazione e funzioni riutilizzabili
    • Evita codice hard-coded in main.py. (come, ad esempio, la password per ADMIN)
    • Organizza le funzioni per responsabilità .
    • Aggiungi commenti e docstring essenziali.

## ⚪ Step 7 – Refactoring e migliorie finali
    • Cura dettagli, naming, commenti, test manuali.
    • Bonus: ordinamento task, cancellazione, stampa bacheca.
    • Progetto pronto per essere consegnato.

## 🔥 Bonus 1: Interfaccia web con Flask (+15 pt)
    • Realizza una versione web con Flask (login, lista task, aggiunta e modifica) a tema Dune (il romanzo di Frank Herbert).
    • Valutazione: semplicità , correttezza, uso di render_template, request, redirect.
    - usa la possibilità di accedere a RawGraphs per visualizzare i dati in grafici interattivi.
