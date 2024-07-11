import re

from bottle import HTTPError, default_app, request

from ...web.app import CustomBottle
from . import functions as pgconf_functions

bottle = CustomBottle()


@bottle.post("/reload")
def post_reload(pgconn):
    """Reload Postgres configuration."""
    default_app().push_audit_notification("PostgreSQL configuration reload.")
    pgconn.execute("SELECT pg_reload_conf();")


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
    current = get_configuration_category(pgconn, None)
    return pgconf_functions.post_settings(
        default_app().temboard, pgconn, current, request.json["settings"]
    )


@bottle.get("/configuration/status")
def get_status(pgconn):
    return pgconf_functions.get_settings_status(pgconn)
