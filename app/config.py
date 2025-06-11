import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_SERVER = os.environ.get('DB_SERVER')