"""
Progetto Arrakis - Web Interface con Flask
Tema Dune (Frank Herbert) + RawGraphs Visualization
"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from functools import wraps
from model import User, Admin, Task, Dataset
from controller import (
    AuthController, TaskController, AdminTaskController, UserController,
    DatasetController, AdminDatasetController
)
from db import get_database
from config import ADMIN_USERNAME, ADMIN_PASSWORD

app = Flask(__name__, template_folder='templates')
app.secret_key = 'arrakis_secret_key_desert_power'

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'db', 'json', 'xml', 'sql', 'txt'}


def login_required(f):
    """Decorator per proteggere le route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator per proteggere le route admin-only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Accesso negato. Solo admin.", 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Restituisce l'utente corrente dalla sessione."""
    if 'user_id' in session:
        db = get_database()
        return db.get_user_by_id(session['user_id'])
    return None


def get_current_admin():
    """Restituisce l'admin corrente dalla sessione."""
    if 'admin_id' in session:
        db = get_database()
        return db.get_admin_by_id(session['admin_id'])
    return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina di login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        is_admin = request.form.get('is_admin') == 'on'

        if is_admin:
            success, message, admin = AuthController.login_admin(username, password)
            if success:
                session['admin_id'] = admin.admin_id
                session['username'] = admin.username
                session['is_admin'] = True
                return redirect(url_for('dashboard'))
        else:
            success, message, user = AuthController.login_user(username, password)
            if success:
                session['user_id'] = user.user_id
                session['username'] = user.username
                session['is_admin'] = False
                return redirect(url_for('dashboard'))

        flash(message, 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Pagina di registrazione."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if password != confirm:
            flash("Le password non coincidono", 'error')
            return render_template('register.html')

        success, message = AuthController.register_user(username, password, email)
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')

    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principale."""
    user = get_current_user()
    admin = get_current_admin()

    if admin:
        tasks = AdminTaskController.get_all_tasks()
        users = UserController.get_all_users()
        datasets = AdminDatasetController.get_all_datasets()
        return render_template('dashboard_admin.html', tasks=tasks, users=users, admin=admin, datasets=datasets)

    if user:
        tasks = TaskController.get_user_tasks(user)
        datasets = DatasetController.get_user_datasets(user)
        return render_template('dashboard.html', tasks=tasks, user=user, datasets=datasets)

    return redirect(url_for('login'))


@app.route('/data')
@login_required
def data_page():
    """Pagina di gestione dati (Tableau-like)."""
    user = get_current_user()
    admin = get_current_admin()

    if admin:
        datasets = AdminDatasetController.get_all_datasets()
        users = UserController.get_all_users()
        return render_template('data_admin.html', datasets=datasets, users=users, admin=admin)

    if user:
        datasets = DatasetController.get_user_datasets(user)
        return render_template('data.html', datasets=datasets, user=user)

    return redirect(url_for('login'))


@app.route('/data/upload', methods=['GET', 'POST'])
@login_required
def upload_dataset():
    """Carica un nuovo dataset."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Nessun file selezionato", 'error')
            return redirect(url_for('data_page'))

        file = request.files['file']
        if file.filename == '':
            flash("Nessun file selezionato", 'error')
            return redirect(url_for('data_page'))

        nome = request.form.get('nome', '').strip()
        descrizione = request.form.get('descrizione', '').strip()

        if not nome:
            flash("Il nome del dataset è obbligatorio", 'error')
            return redirect(url_for('data_page'))

        if file and allowed_file(file.filename):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            try:
                success, message, dataset = DatasetController.upload_dataset(
                    tmp_path, file.filename, nome, descrizione, user
                )
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'error')
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            return redirect(url_for('data_page'))

    return render_template('upload_dataset.html', user=user)


@app.route('/data/<int:dataset_id>/visualize')
@login_required
def visualize_dataset(dataset_id):
    """Visualizza dataset con RawGraphs."""
    user = get_current_user()
    admin = get_current_admin()

    if admin:
        dataset = AdminDatasetController.get_dataset_by_id(dataset_id)
        if not dataset:
            flash("Dataset non trovato", 'error')
            return redirect(url_for('dashboard'))
        success, csv_data, error = AdminDatasetController.get_dataset_data_admin(dataset_id)
    else:
        dataset = DatasetController.get_dataset_by_id(dataset_id, user)
        if not dataset:
            flash("Dataset non trovato", 'error')
            return redirect(url_for('dashboard'))
        success, csv_data, error = DatasetController.get_dataset_data(dataset_id, user)

    if not success:
        flash(error, 'error')
        return redirect(url_for('data_page'))

    return render_template('visualize.html', dataset=dataset, csv_data=csv_data)


@app.route('/data/<int:dataset_id>/preview')
@login_required
def preview_dataset(dataset_id):
    """Preview dataset in formato tabella."""
    user = get_current_user()
    admin = get_current_admin()

    if admin:
        dataset = AdminDatasetController.get_dataset_by_id(dataset_id)
        if not dataset:
            return "Dataset non trovato", 404
        success, csv_data, error = AdminDatasetController.get_dataset_data_admin(dataset_id)
    else:
        dataset = DatasetController.get_dataset_by_id(dataset_id, user)
        if not dataset:
            return "Dataset non trovato", 404
        success, csv_data, error = DatasetController.get_dataset_data(dataset_id, user)

    if not success:
        return f"Errore: {error}", 500

    return render_template('preview.html', dataset=dataset, csv_data=csv_data)


@app.route('/data/<int:dataset_id>/delete', methods=['POST'])
@login_required
def delete_dataset(dataset_id):
    """Elimina un dataset."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    success, message = DatasetController.delete_dataset(dataset_id, user)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('data_page'))


@app.route('/data/<int:dataset_id>/csv')
@login_required
def download_csv(dataset_id):
    """Scarica dataset in formato CSV."""
    user = get_current_user()
    admin = get_current_admin()

    if admin:
        success, csv_data, error = AdminDatasetController.get_dataset_data_admin(dataset_id)
    else:
        success, csv_data, error = DatasetController.get_dataset_data(dataset_id, user)

    if not success:
        flash(error, 'error')
        return redirect(url_for('data_page'))

    import io
    output = io.StringIO(csv_data)

    return send_file(
        io.BytesIO(csv_data.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{dataset_id}_data.csv"
    )


@app.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """Crea un nuovo task."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        titolo = request.form.get('titolo', '').strip()
        descrizione = request.form.get('descrizione', '').strip()
        stato = request.form.get('stato', 'todo')

        success, message, task = TaskController.create_task(
            titolo, descrizione, stato, user
        )

        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')

        return redirect(url_for('dashboard'))

    return render_template('create_task.html')


@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Modifica un task."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    task = TaskController.get_task_by_id(task_id, user)
    if not task:
        flash("Task non trovato", 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        titolo = request.form.get('titolo', '').strip()
        descrizione = request.form.get('descrizione', '').strip()
        stato = request.form.get('stato', '')

        success, message = TaskController.update_task(
            task_id, user, titolo=titolo, descrizione=descrizione, stato=stato
        )

        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')

        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task)


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Elimina un task."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    success, message = TaskController.delete_task(task_id, user)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('dashboard'))


@app.route('/tasks/filter/<stato>')
@login_required
def filter_tasks(stato):
    """Filtra task per stato."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    tasks = TaskController.get_tasks_by_status(user, stato)
    return render_template('dashboard.html', tasks=tasks, user=user, filter_stato=stato)


@app.route('/admin/tasks/<int:task_id>/update_status', methods=['POST'])
@login_required
def admin_update_task_status(task_id):
    """Admin aggiorna stato task."""
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('login'))

    stato = request.form.get('stato', '')
    success, message = AdminTaskController.update_task_status(task_id, stato, admin)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('dashboard'))


@app.route('/admin/users/<int:user_id>/tasks')
@login_required
def admin_user_tasks(user_id):
    """Admin visualizza task di un utente."""
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('login'))

    user = UserController.get_user_by_id(user_id)
    if not user:
        flash("Utente non trovato", 'error')
        return redirect(url_for('dashboard'))

    tasks = AdminTaskController.get_user_tasks(user_id)
    return render_template('admin_user_tasks.html', tasks=tasks, target_user=user, admin=admin)


@app.route('/admin/users/<int:user_id>/datasets')
@login_required
def admin_user_datasets(user_id):
    """Admin visualizza dataset di un utente."""
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('login'))

    user = UserController.get_user_by_id(user_id)
    if not user:
        flash("Utente non trovato", 'error')
        return redirect(url_for('dashboard'))

    datasets = AdminDatasetController.get_user_datasets(user_id)
    return render_template('admin_user_datasets.html', datasets=datasets, target_user=user, admin=admin)


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Admin elimina utente."""
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('login'))

    success, message = UserController.delete_user(user_id, admin)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('dashboard'))


def init_app():
    """Inizializza l'applicazione."""
    AuthController.init_admin()


if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
