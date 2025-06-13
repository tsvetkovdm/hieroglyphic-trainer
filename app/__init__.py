from flask import Flask
from flask_bootstrap import Bootstrap5
from app.config import Config

app = Flask(__name__)

bootstrap = Bootstrap5(app)

app.config.from_object(Config)

from app import routes