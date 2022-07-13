from flask import Flask, g

from ..model import Session


def create_app(temboard_app):
    app = Flask('temboardui', static_folder=None)
    app.temboard = temboard_app
    SQLAlchemy(app)
    return app


class SQLAlchemy(object):
    # Flask extension to manage a SQLAlchemy session per request.
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.db = self
        app.before_request(self.before)
        app.teardown_request(self.teardown)

    def before(self):
        g.db_session = Session()

    def teardown(self, error):
        if error:
            # Expunge objects before rollback to implement
            # expire_on_rollback=False. This allow templates to reuse
            # request.instance object and joined object without triggering lazy
            # load.
            g.db_session.expunge_all()
            g.db_session.rollback()
        else:
            g.db_session.commit()

        g.db_session.close()
        del g.db_session
