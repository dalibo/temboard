import logging

from bottle import Bottle, default_app, HTTPError

from ...tools import now
from ...toolkit.configuration import OptionSpec


bottle = Bottle()
logger = logging.getLogger(__name__)


query = """\
SELECT
  rolname,
  datname,
  pgss.*
FROM pg_stat_statements pgss
JOIN pg_authid ON pgss.userid = pg_authid.oid
JOIN pg_database ON pgss.dbid = pg_database.oid
"""


@bottle.get("/")
def get_statements(pgpool):
    """Return a snapshot of latest statistics of executed SQL statements
    """
    app = default_app().temboard
    config = app.config
    dbname = config.statements.dbname
    snapshot_datetime = now()
    try:
        conn = pgpool.getconn(dbname)
        data = list(conn.query(query))
    except Exception as e:
        discover = app.discover.ensure_latest()
        pg_version = discover['postgres']['version_num']
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


class StatementsPlugin:
    PG_MIN_VERSION = (90500, 9.5)
    s = "statements"
    option_specs = [OptionSpec(s, "dbname", default="postgres")]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def load(self):
        default_app().mount('/statements', bottle)

    def unload(self):
        self.app.config.remove_specs(self.option_specs)
