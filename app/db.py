from app import app
import psycopg

def get_connection():
    return psycopg.connect(host=app.config['DB_SERVER'],
                           user=app.config['DB_USER'],
                           password=app.config['DB_PASSWORD'],
                           dbname=app.config['DB_NAME'],
                           client_encoding='UTF-8')