from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from app.forms import RegistrationForm, LoginForm, EditUserForm
from app.user_model import User
from app.db import get_connection
from flask import render_template, redirect, flash, url_for, request, abort
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlsplit
from functools import wraps

DEFAULT_ROLE_ID = 2

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 1:  # предполагаем, что id=1 — это "admin"
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
                    SELECT u.id, u.username, u.email, r.name
                    FROM "user" as u
                    LEFT JOIN "role" as r
                    ON u.role_id = r.id 
                    ''')
        users = cur.fetchall()
    return render_template('admin/admin_dashboard.html', users=users)

@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    form = EditUserForm()
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute('SELECT id, name FROM "role"')
        roles = cur.fetchall()
        form.role_id.choices = [(r[0], r[1]) for r in roles]

        if request.method == 'GET':
            cur.execute('''
                        SELECT email, first_name, last_name, date_of_birth, want_spam, role_id
                        FROM "user" 
                        WHERE id = %s
                        ''', (user_id,))
            user_data = cur.fetchone()
            if user_data:
                form.email.data = user_data[0]
                form.first_name.data = user_data[1]
                form.last_name.data = user_data[2]
                form.date_of_birth.data = user_data[3]
                form.want_spam.data = user_data[4]
                form.role_id.data = user_data[5]

        elif form.validate_on_submit():
            cur.execute('''
                        UPDATE "user"
                        SET email=%s, first_name=%s, last_name=%s, date_of_birth=%s, want_spam=%s, role_id=%s
                        WHERE id = %s
                        ''', 
                        (form.email.data,
                         form.first_name.data,
                         form.last_name.data,
                         form.date_of_birth.data,
                         form.want_spam.data,
                         form.role_id.data,
                         user_id))
            conn.commit()
            flash('Пользователь обновлён', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_user.html', form=form)

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('Вы не можете удалить сами себя.', 'warning')
        return redirect(url_for('admin_dashboard'))

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM "user" WHERE id = %s', (user_id,))
        if cur.fetchone() is None:
            flash('Пользователь не найден.', 'danger')
            return redirect(url_for('admin_dashboard'))

        cur.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
        flash('Пользователь удалён.', 'success')
        return redirect(url_for('admin_dashboard'))

@app.route('/testdb')
def test_connection():
    try:
        with get_connection():
            flash("Подключение к БД успешно", "success")
    except Exception as e:
        flash(f"Ошибка подключения к БД: {e}", "danger")
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        email = reg_form.email.data
        password = reg_form.password.data
        first_name = reg_form.first_name.data
        last_name = reg_form.last_name.data
        date_of_birth = reg_form.date_of_birth.data

        password_hash = generate_password_hash(password)

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM "user" WHERE username = %s OR email = %s', (username, email))

            if cur.fetchone():
                flash("Пользователь с таким именем или email уже существует", "danger")
                return redirect(url_for('register'))
            
            cur.execute('''
                        INSERT INTO "user" 
                        (username, password, first_name, last_name, email, date_of_birth, role_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', 
                        (username, 
                         password_hash, 
                         first_name, 
                         last_name, 
                         email, 
                         date_of_birth, 
                         DEFAULT_ROLE_ID))
            
            flash (f'Регистрация {reg_form.username.data} успешна', 'success')
            return redirect(url_for('login'))
        
    return render_template('registration.html', title='Регистрация', form=reg_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                        SELECT id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id
                        FROM "user" 
                        WHERE username = %s
                        ''', (login_form.username.data,))
            result = cur.fetchone()

        if result is None or not check_password_hash(result[2], login_form.password.data):
            flash('Попытка входа неудачна или пользователя не существует(', 'danger')
            return redirect(url_for('login'))
        
        id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id = result
        user = User(id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id)
        login_user(user, remember=login_form.remember_me.data)
        flash(f'Вы успешно вошли в систему, {current_user.username}', 'success')

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', title='Вход', form=login_form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = EditUserForm()

    if request.method == 'GET':
        profile_form.email.data = current_user.email
        profile_form.first_name.data = current_user.first_name
        profile_form.last_name.data = current_user.last_name
        profile_form.date_of_birth.data = current_user.date_of_birth
        profile_form.want_spam.data = getattr(current_user, 'want_spam', False)
    
    if profile_form.validate_on_submit():
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                        UPDATE "user" 
                        SET email=%s, first_name=%s, last_name=%s, date_of_birth=%s, want_spam=%s
                        WHERE id=%s
                        ''',
                        (profile_form.email.data,
                         profile_form.first_name.data,
                         profile_form.last_name.data,
                         profile_form.date_of_birth.data,
                         profile_form.want_spam.data,
                         current_user.id))
            flash('Профиль успешно изменен', 'success')
            return redirect(url_for('profile'))
    return render_template('profile.html', form=profile_form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))             

@app.route('/numbers-quantities')
@login_required
def get_num_quan_group():
    rad_group = 'numbers-quantities'
    with get_connection() as conn:
        cur = conn.cursor()
        rad_symbols = cur.execute('''
                                  SELECT 
                                  lo.symbol, 
                                  lo.pinyin, 
                                  lo.meaning, 
                                  rg.name, 
                                  rg.slug 
                                  FROM "learning_object" AS lo 
                                  INNER JOIN "radical_group" AS rg ON rg.id = lo.group_id 
                                  WHERE rg.slug LIKE %s
                                  ''', (rad_group,)).fetchall()
        
        return render_template('radicals.html', title='Радикалы группы "Числа и количество"',
                               rad_symbols=rad_symbols)