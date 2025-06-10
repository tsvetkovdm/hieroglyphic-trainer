from app import app

@app.route('/')
def hello_world():
    return "Hi, do you wanna learn some chinese characters?:/"