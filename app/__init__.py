from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap5(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

from app.routes.main import main
from app.routes.auth import auth
from app.routes.admin import admin

app.register_blueprint(main)
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(admin, url_prefix='/admin')

with app.test_request_context():
    print(app.url_map)