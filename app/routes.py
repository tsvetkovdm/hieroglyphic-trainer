from app import app
from flask import render_template
import psycopg

@app.route('/')
def index():
    return "Hi, do you wanna learn some chinese characters?:/"

@app.route('/testdb')
def test_connection():
    con = None
    message = ""
    try:
        con = psycopg.connect(host=app.config['DB_SERVER'],
                              user=app.config['DB_USER'],
                              password=app.config['DB_PASSWORD'],
                              dbname=app.config['DB_NAME'])
    except Exception as e:
        message = f"Ошибка подключения: {e}"
    else:
        message = "Подключение успешно"
    finally:
        if con:
            con.close()
        return message

@app.route('/numbers-quantities')
def get_num_quan_group():
    rad_group = 'numbers-quantities'
    with psycopg.connect(host=app.config['DB_SERVER'],
                         user=app.config['DB_USER'],
                         password=app.config['DB_PASSWORD'],
                         dbname=app.config['DB_NAME']) as con:
        cur=con.cursor()
        rad_symbols = cur.execute(f'SELECT lo.symbol, lo.pinyin, lo.meaning, rg.name, rg.slug FROM "learning_object" AS lo INNER JOIN "radical_group" AS rg ON rg.id = lo.group_id WHERE rg.slug LIKE %s', 
                                  (rad_group,)).fetchall()
        return render_template('radicals.html', title='Радикалы группы "Числа и количество"',
                               rad_symbols=rad_symbols)
