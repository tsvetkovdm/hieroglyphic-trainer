from flask import Blueprint, render_template, redirect, flash, url_for, request, abort
from flask_login import current_user
from app.routes import admin
from app.forms import EditUserForm
from app.db import get_connection
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 1:  # предполагаем, что id=1 — это "admin"
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
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

@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
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
            return redirect(url_for('admin_dashboard'))

    return render_template('profile.html', form=form, title=f'Редактировать профиль {user_data[0]}', show_role = True)

@admin.route('/user/delete/<int:user_id>', methods=['POST'])
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
