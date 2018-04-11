from temboardagent.errors import UserError
from temboardagent.routing import add_route

from . import functions as pgconf_functions
from .types import (
    T_PGSETTINGS_CATEGORY,
)


def get_pg_conf(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_settings(conn, http_context)


def get_pg_conf_categories(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_settings_categories(conn)


def post_pg_conf(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_settings(conn, app.config, http_context)


def get_pg_conf_status(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_settings_status(conn)


def get_pg_hba(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba(conn, http_context)


def get_pg_hba_raw(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba_raw(conn, http_context)


def post_pg_hba(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_hba(conn, app.config, http_context)


def post_pg_hba_raw(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_hba_raw(conn, app.config, http_context)


def delete_pg_hba(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.delete_hba_version(conn, app.config,
                                                   http_context)


def get_pg_hba_versions(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba_versions(conn)


def get_pg_ident(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_pg_ident(conn)


def post_pg_ident(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.post_pg_ident(conn, app.config, http_context)


def get_hba_options(http_context, app):
    with app.postgres.connect() as conn:
        return pgconf_functions.get_hba_options(conn)


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

        add_route('GET', '/pgconf/configuration')(get_pg_conf)
        add_route('GET', '/pgconf/configuration/categories')(
            get_pg_conf_categories)
        add_route('GET',
                  '/pgconf/configuration/category/' + T_PGSETTINGS_CATEGORY)(
            get_pg_conf)
        add_route('GET', '/pgconf/configuration/status')(get_pg_conf_status)
        add_route('GET', '/pgconf/hba')(get_pg_hba)
        add_route('GET', '/pgconf/hba/raw')(get_pg_hba_raw)
        add_route('GET', '/pgconf/hba/versions')(get_pg_hba_versions)
        add_route('GET', '/pgconf/pg_ident')(get_pg_ident)
        add_route('GET', '/pgconf/hba/options')(get_hba_options)
        add_route('POST', '/pgconf/hba')(post_pg_hba)
        add_route('POST', '/pgconf/hba/raw')(post_pg_hba_raw)
        add_route('POST', '/pgconf/configuration')(post_pg_conf)
        add_route('POST', '/pgconf/pg_ident')(post_pg_ident)
        add_route('DELETE', '/pgconf/hba')(delete_pg_hba)

    def unload(self):
        pass
