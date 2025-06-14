from app.forms import RegistrationForm
from app import app
from flask import render_template
import psycopg

def get_db():
    return psycopg.connect(host=app.config['DB_SERVER'],
                           user=app.config['DB_USER'],
                           password=app.config['DB_PASSWORD'],
                           dbname=app.config['DB_NAME'])

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

#@app.get('/register')
#def register():
#    reg_form = RegistrationForm()
#    return render_template('registration.html', title='Регистрация', form=reg_form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        email = reg_form.email.data
        password = reg_form.password.data
        first_name = reg_form.first_name.data
        last_name = reg_form.last_name.data
        date_of_birth = reg_form.date_of_birth.data
        try:
            con = get_db()
            cur = con.cursor()
            cur.execute('INSERT INTO "user" (username, password, first_name, last_name, email, date_of_birth, role_id) VALUES (%s, %s, %s, %s, %s, %s, %s)', (username, password, first_name, last_name, email, date_of_birth, '2'))
            con.commit()
            cur.close()
            return f'Регистрация {reg_form.username.data} успешна'
        except psycopg.IntegrityError as e:
            con.rollback()  # откатываем транзакцию при ошибке
            return "Пользователь или email уже существует", 400
        finally:
            cur.close()
    return render_template('registration.html', title='Регистрация', form=reg_form)