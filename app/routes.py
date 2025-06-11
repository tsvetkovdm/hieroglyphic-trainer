from app import app
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