from flask import current_app as app, redirect


@app.route('/')
def index():
    return redirect('/home')
