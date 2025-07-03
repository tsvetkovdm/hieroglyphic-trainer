from flask import Blueprint, render_template, redirect, flash, url_for
from flask_login import login_required
from app.db import get_connection

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/testdb')
def test_connection():
    try:
        with get_connection():
            flash("Подключение к БД успешно", "success")
    except Exception as e:
        flash(f"Ошибка подключения к БД: {e}", "danger")
    return redirect(url_for('main.index'))

@main.route('/numbers-quantities')
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