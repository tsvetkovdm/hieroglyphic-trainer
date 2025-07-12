from werkzeug.security import generate_password_hash
from flask import Blueprint, render_template, redirect, flash, url_for, request, abort
from flask_login import current_user
from app.forms import AdminEditUserForm, AdminCreateUserForm
from app.db import get_connection
from functools import wraps

admin = Blueprint('admin', __name__)

DEFAULT_ROLE_ID = 2

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 1:  # предполагаем, что id=1 — это "admin"
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def dashboard():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
                    SELECT u.id, u.username, u.email, r.name
                    FROM "user" as u
                    LEFT JOIN "role" as r
                    ON u.role_id = r.id 
                    ''')
        users = cur.fetchall()
    return render_template('admin/dashboard.html', users=users)

@admin.route('/user/add/', methods=['GET', 'POST'])
@admin_required
def add_user():
    form = AdminCreateUserForm()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, name FROM "role"')
        roles = cur.fetchall()
        form.role_id.choices = [(r[0], r[1]) for r in roles]

        if form.validate_on_submit():
            cur.execute('SELECT id FROM "user" WHERE username = %s OR email = %s',
                        (form.username.data, form.email.data))
            if cur.fetchone():
                flash("Пользователь с таким именем или email уже существует", "danger")
                return redirect(url_for('admin.add_user'))

            password_hash = generate_password_hash(form.password.data)
            cur.execute('''
                        INSERT INTO "user" 
                        (username, password, first_name, last_name, 
                        email, date_of_birth, want_spam, role_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''',
                        (form.username.data, password_hash, 
                         form.first_name.data, form.last_name.data, 
                         form.email.data, form.date_of_birth.data, 
                         form.want_spam.data, form.role_id.data))
            conn.commit()

            flash(f'Пользователь {form.username.data} успешно создан', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_user.html', form=form, title=f'Создание пользователя')

@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    form = AdminEditUserForm()
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute('SELECT id, name FROM "role"')
        roles = cur.fetchall()
        form.role_id.choices = [(r[0], r[1]) for r in roles]

        if request.method == 'GET':
            cur.execute('''
                        SELECT username, email, first_name, last_name, date_of_birth, want_spam, role_id
                        FROM "user" 
                        WHERE id = %s
                        ''', (user_id,))
            user_data = cur.fetchone()
            if user_data:
                form.email.data = user_data[1]
                form.first_name.data = user_data[2]
                form.last_name.data = user_data[3]
                form.date_of_birth.data = user_data[4]
                form.want_spam.data = user_data[5]
                form.role_id.data = user_data[6]

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
            return redirect(url_for('admin.dashboard'))

    return render_template('profile.html', form=form, title=f'Редактировать профиль {user_data[0]}', show_role = True)

@admin.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Вы не можете удалить сами себя.', 'warning')
        return redirect(url_for('admin.dashboard'))

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM "user" WHERE id = %s', (user_id,))
        if cur.fetchone() is None:
            flash('Пользователь не найден.', 'danger')
            return redirect(url_for('admin.dashboard'))

        cur.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
        flash('Пользователь удалён.', 'success')
        return redirect(url_for('admin.dashboard'))
