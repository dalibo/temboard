from bottle import default_app


class PgConfPlugin:
    PG_MIN_VERSION = (90500, 9.5)

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        from .routes import bottle

        default_app().mount("/pgconf/", bottle)
