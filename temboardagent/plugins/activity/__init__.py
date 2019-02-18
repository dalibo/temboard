from temboardagent.errors import UserError
from temboardagent.routing import RouteSet

from . import functions as activity_functions


routes = RouteSet()


@routes.get(b'/activity', check_key=True)
def get_activity(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.get_activity(conn)


@routes.get(b'/activity/waiting', check_key=True)
def get_activity_waiting(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.get_activity_waiting(conn)


@routes.get(b'/activity/blocking', check_key=True)
def get_activity_blocking(http_context, app):
    with app.postgres.connect() as conn:
        return activity_functions.get_activity_blocking(conn)


@routes.post(b'/activity/kill')
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

        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
