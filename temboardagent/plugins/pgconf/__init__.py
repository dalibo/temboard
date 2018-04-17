from temboardagent.errors import UserError
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


@routes.get(b'/hba')
def get_pg_hba(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba(conn, http_context)


@routes.post(b'/hba')
def post_pg_hba(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_hba(conn, app.config, http_context)


@routes.delete(b'/hba')
def delete_pg_hba(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.delete_hba_version(conn, app.config,
                                                   http_context)


@routes.get(b'/hba/raw')
def get_pg_hba_raw(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba_raw(conn, http_context)


@routes.post(b'/hba/raw')
def post_pg_hba_raw(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_hba_raw(conn, app.config, http_context)


@routes.get(b'/hba/options')
def get_hba_options(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba_options(conn)


@routes.get(b'/hba/versions')
def get_pg_hba_versions(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba_versions(conn)


@routes.get(b'/pg_ident')
def get_pg_ident(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_pg_ident(conn)


@routes.post(b'/pg_ident')
def post_pg_ident(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_pg_ident(conn, app.config, http_context)


class PgConfPlugin(object):
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
