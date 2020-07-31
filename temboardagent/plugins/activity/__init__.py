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
    PG_MIN_VERSION = (90400, 9.4)

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
