from temboardagent.errors import UserError
from temboardagent.routing import add_route

from . import functions as activity_functions


def get_activity(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.get_activity(conn)


def get_activity_waiting(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.get_activity_waiting(conn)


def get_activity_blocking(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.get_activity_blocking(conn)


def post_activity_kill(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.post_activity_kill(conn, app.config,
                                                     http_context)


class ActivityPlugin(object):
    PG_MIN_VERSION = 90400

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        pg_version = self.app.postgres.fetch_version()
        if pg_version < self.PG_MIN_VERSION:
            msg = "%s is incompatible with Postgres below 9.4" % (
                self.__class__.__name__)
            raise UserError(msg)

        add_route('GET', '/activity')(get_activity)
        add_route('GET', '/activity/waiting')(get_activity_waiting)
        add_route('GET', '/activity/blocking')(get_activity_blocking)
        add_route('POST', '/activity/kill')(post_activity_kill)

    def unload(self):
        pass
