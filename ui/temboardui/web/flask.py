from flask import Flask


def create_app(temboard_app):
    app = Flask('temboardui', static_folder=None)
    app.temboard = temboard_app
    return app
