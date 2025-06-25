from app import login_manager
from app.db import get_connection
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(id):
    with get_connection() as con:
        cur = con.cursor()
        result = cur.execute('SELECT username, password '
                                         'From "user" '
                                         'WHERE id = %s', (id,)).fetchone()
    if result:
        username, password = result
        return User(id, username, password)
    return None