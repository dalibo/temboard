import re

import psycopg2.sql
from bottle import HTTPError, default_app, request

from ...queries import QUERIES
from ...web.app import CustomBottle
from . import functions as pgconf_functions

bottle = CustomBottle()


@bottle.post("/reload")
def post_reload(pgconn):
    """Reload Postgres configuration."""
    default_app().push_audit_notification("PostgreSQL configuration reload.")
    pgconn.execute("SELECT pg_reload_conf();")


@bottle.get("/settings")
def get_settings(pgconn):
    """Return all settings metadata."""
    return list(pgconn.query(QUERIES["pgconf-settings"]))


@bottle.post("/settings")
def post_settings(pgconn, new=None):
    """Applies a JSON mapping of setting -> value."""
    new = request.json if new is None else new
    if not hasattr(new, "items"):
        raise HTTPError(406, "Requires a mapping of settings and values.")
    if not new:
        raise HTTPError(406, "No settings.")

    for name, setting in new.items():
        if setting is None:
            raise HTTPError(406, "Setting value is required.")
        if len(setting) > 1024:
            raise HTTPError(406, "Setting value is too long.")

        default_app().push_audit_notification(f"Setting {name} to {setting}.")
        sql = psycopg2.sql.SQL("""ALTER SYSTEM SET {} TO %(setting)s;""")
        try:
            pgconn.execute(
                sql.format(psycopg2.sql.Identifier(name)), {"setting": setting}
            )
        except psycopg2.DatabaseError as e:
            return HTTPError(406, e.pgerror)

    post_reload(pgconn)


@bottle.delete("/settings/<name>")
def delete_settings(pgconn, name):
    """Restore settings to default."""
    default_app().push_audit_notification(f"Restoring {name} to default.")
    sql = psycopg2.sql.SQL("""ALTER SYSTEM SET {} TO DEFAULT;""")
    try:
        pgconn.execute(sql.format(psycopg2.sql.Identifier(name)))
    except psycopg2.DatabaseError as e:
        return HTTPError(406, e.pgerror)

    post_reload(pgconn)


@bottle.post("/settings/<name>/reset")
def post_settings_reset(pgconn, name):
    """Reset settings to current value."""
    default_app().push_audit_notification(f"Reseting {name} to current.")
    sql = psycopg2.sql.SQL("""ALTER SYSTEM RESET {};""")
    try:
        pgconn.execute(sql.format(psycopg2.sql.Identifier(name)))
    except psycopg2.DatabaseError as e:
        return HTTPError(406, e.pgerror)

    post_reload(pgconn)


# DEPRECATED: Remove these routes once UI uses only the above.


@bottle.get("/configuration")
def get_configuration(pgconn):
    return get_configuration_category(pgconn, None)


@bottle.get("/configuration/category/<category:path>")
def get_configuration_category(pgconn, category):
    search = None
    if "filter" in request.query:
        if not re.match("([a-zA-Z0-9_]{3,128})", request.query["filter"]):
            raise HTTPError(406, "Parameter 'filter' is malformed")
        search = request.query["filter"]
    if category:
        # Unquote +.
        category = category.replace("+", " ")
    return pgconf_functions.get_settings(pgconn, category, search)


@bottle.get("/configuration/categories")
def get_configuration_categories(pgconn):
    return pgconf_functions.get_settings_categories(pgconn)


@bottle.post("/configuration")
def post_configuration(pgconn):
    if "settings" not in request.json:
        raise HTTPError(406, "Parameter 'settings' not sent.")
    reset = {i["name"] for i in request.json["settings"] if not i["setting"]}
    for name in reset:
        out = post_settings_reset(pgconn, name)
        if out:
            return out

    # Transpose to new payload format.
    new = {
        i["name"]: i["setting"]
        for i in request.json["settings"]
        if i["name"] not in reset
    }
    if new:
        out = post_settings(pgconn, new)

    if out is None:
        out = {"settings": []}
    return out


@bottle.get("/configuration/status")
def get_status(pgconn):
    return pgconf_functions.get_settings_status(pgconn)
