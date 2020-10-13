import logging

from temboardagent.errors import HTTPError
from temboardagent.routing import RouteSet
from temboardagent.postgres import Postgres
from temboardagent.tools import now
from temboardagent.toolkit.configuration import OptionSpec


logger = logging.getLogger(__name__)
routes = RouteSet(prefix=b"/statements")


query = """\
SELECT
  rolname,
  datname,
  pgss.*
FROM pg_stat_statements pgss
JOIN pg_authid ON pgss.userid = pg_authid.oid
JOIN pg_database ON pgss.dbid = pg_database.oid
"""


@routes.get(b"/", check_key=True)
def get_statements(http_context, app):
    """Return a snapshot of latest statistics of executed SQL statements
    """
    config = app.config
    dbname = config.statements.dbname
    snapshot_datetime = now()
    conninfo = dict(config.postgresql, dbname=dbname)
    try:
        with Postgres(**conninfo).connect() as conn:
            data = list(conn.query(query))
    except Exception as e:
        pg_version = app.postgres.fetch_version()
        if (
            pg_version < 90600 or
            'relation "pg_stat_statements" does not exist' in str(e)
        ):
            raise HTTPError(
                404, "pg_stat_statements not enabled on database %s" % dbname
            )
        logger.error(
            "Failed to get pg_stat_statements data on database %s: %s",
            dbname,
            e,
        )
        raise HTTPError(500, e)
    else:
        return {"snapshot_datetime": snapshot_datetime, "data": data}


class StatementsPlugin(object):
    PG_MIN_VERSION = (90500, 9.5)
    s = "statements"
    option_specs = [OptionSpec(s, "dbname", default="postgres")]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def load(self):
        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.option_specs)
