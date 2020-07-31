from temboardagent.routing import RouteSet

from . import functions as pgconf_functions
from .types import (
    T_PGSETTINGS_CATEGORY,
)


routes = RouteSet(prefix=b'/pgconf')


@routes.get(b'/configuration')
@routes.get(b'/configuration/category/' + T_PGSETTINGS_CATEGORY)
def get_pg_conf(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_settings(conn, http_context)


@routes.get(b'/configuration/categories')
def get_pg_conf_categories(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_settings_categories(conn)


@routes.post(b'/configuration')
def post_pg_conf(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_settings(conn, app.config, http_context)


@routes.get(b'/configuration/status')
def get_pg_conf_status(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_settings_status(conn)


class PgConfPlugin(object):
    PG_MIN_VERSION = (90500, 9.5)

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
