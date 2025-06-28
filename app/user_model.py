from app import login_manager
from app.db import get_connection
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.want_spam = want_spam
        self.role_id = role_id
    
    @property
    def is_admin(self):
        return self.role_id == 1

@login_manager.user_loader
def load_user(id):
    with get_connection() as conn:
        cur = conn.cursor()
        result = cur.execute('''SELECT username, password, email, first_name, last_name, date_of_birth, want_spam, role_id
                             From "user" WHERE id = %s''', (id,)).fetchone()
    if result:
        username, password, email, first_name, last_name, date_of_birth, want_spam, role_id = result
        return User(id, username, password, email, first_name, last_name, date_of_birth, want_spam, role_id)
    return None

