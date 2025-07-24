from flask import Blueprint, render_template, redirect, flash, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_connection
from app.forms import RegistrationForm, LoginForm, EditUserForm
from app.user_model import User
from urllib.parse import urlsplit

auth = Blueprint('auth', __name__)

DEFAULT_ROLE_ID = 2

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        date_of_birth = form.date_of_birth.data

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
            
            flash (f'Регистрация {form.username.data} успешна', 'success')
            return redirect(url_for('auth.login'))
        
    return render_template('auth/registration.html', title='Регистрация', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                        SELECT id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id
                        FROM "user" 
                        WHERE username = %s
                        ''', (form.username.data,))
            result = cur.fetchone()

        if result is None or not check_password_hash(result[2], form.password.data):
            flash('Попытка входа неудачна или пользователя не существует(', 'danger')
            return redirect(url_for('auth.login'))
        
        id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id = result
        user = User(id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id)
        login_user(user, remember=form.remember_me.data)
        flash(f'Вы успешно вошли в систему, {current_user.username}', 'success')

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Вход', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))

@auth.route('/change')
@login_required
def change():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditUserForm()
    
    if request.method == 'GET':
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.date_of_birth.data = current_user.date_of_birth
        form.want_spam.data = getattr(current_user, 'want_spam', False)

    elif form.validate_on_submit():
        with get_connection() as conn:
            cur = conn.cursor()
            print("Form validated")
            cur.execute('''
                        UPDATE "user" 
                        SET email=%s, first_name=%s, last_name=%s, date_of_birth=%s, want_spam=%s
                        WHERE id=%s
                        ''',
                        (form.email.data,
                        form.first_name.data,
                        form.last_name.data,
                        form.date_of_birth.data,
                        form.want_spam.data,
                        current_user.id))
            conn.commit()
            flash('Профиль успешно изменен', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('profile.html', form=form, title=f'Мой профиль', show_role=False)
