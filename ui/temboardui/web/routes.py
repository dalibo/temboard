from flask import current_app as app, redirect

from .flask import anonymous_allowed


@app.route('/')
@anonymous_allowed
def index():
    return redirect('/home')
