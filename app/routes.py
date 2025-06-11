from app import app

@app.route('/')
def index():
    return "Hi, do you wanna learn some chinese characters?:/"