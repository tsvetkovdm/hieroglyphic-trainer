from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from app.forms import RegistrationForm, LoginForm
from app.user import User
from app.db import get_connection
from flask import render_template, redirect, flash, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlsplit
import psycopg

DEFAULT_ROLE_ID = 2

@app.route('/')
def index():
    return render_template('index.html')

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
        password_hash = generate_password_hash(password)
        first_name = reg_form.first_name.data
        last_name = reg_form.last_name.data
        date_of_birth = reg_form.date_of_birth.data

        with get_connection() as con:
            cur = con.cursor()
            cur.execute('SELECT id FROM "user" WHERE username = %s OR email = %s', (username, email))

            if cur.fetchone():
                flash("Пользователь с таким именем или email уже существует", "danger")
                return redirect(url_for('register'))
            
            cur.execute('''INSERT INTO "user" 
                        (username, password, first_name, last_name, email, date_of_birth, role_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                        (username, password_hash, first_name, last_name, email, date_of_birth, DEFAULT_ROLE_ID))
            
            flash (f'Регистрация {reg_form.username.data} успешна', 'success')
            return redirect(url_for('login'))
        
    return render_template('registration.html', title='Регистрация', form=reg_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        with get_connection() as con:
            cur = con.cursor()
            cur.execute('''SELECT id, username, password
                        FROM "user" 
                        WHERE username = %s''', (login_form.username.data,))
            result = cur.fetchone()

        if result is None or not check_password_hash(result[2], login_form.password.data):
            flash('Попытка входа неудачна', 'danger')
            return redirect(url_for('login'))
        
        id, username, password = result
        user = User(id, username, password)
        login_user(user, remember=login_form.remember_me.data)
        flash(f'Вы успешно вошли в систему, {current_user.username}', 'success')

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', title='Вход', form=login_form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

             

@app.route('/numbers-quantities')
@login_required
def get_num_quan_group():
    rad_group = 'numbers-quantities'
    with get_connection() as con:
        cur = con.cursor()
        rad_symbols = cur.execute('''SELECT 
                                  lo.symbol, 
                                  lo.pinyin, 
                                  lo.meaning, 
                                  rg.name, 
                                  rg.slug 
                                  FROM "learning_object" AS lo 
                                  INNER JOIN "radical_group" AS rg ON rg.id = lo.group_id 
                                  WHERE rg.slug LIKE %s''', 
                                  (rad_group,)).fetchall()
        
        return render_template('radicals.html', title='Радикалы группы "Числа и количество"',
                               rad_symbols=rad_symbols)