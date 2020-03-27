import logging

from temboardagent.errors import HTTPError, UserError
from temboardagent.routing import RouteSet
from temboardagent.spc import connector, error
from temboardagent.tools import now
from temboardagent.toolkit.configuration import OptionSpec


logger = logging.getLogger(__name__)
routes = RouteSet(prefix=b"/statements")


query = """\
SELECT
  rolname,
  datname,
  pgss.userid,
  pgss.dbid,
  pgss.queryid,
  pgss.query,
  pgss.calls,
  pgss.total_time,
  pgss.min_time,
  pgss.max_time,
  pgss.mean_time,
  pgss.stddev_time,
  pgss.rows,
  pgss.shared_blks_hit,
  pgss.shared_blks_read,
  pgss.shared_blks_dirtied,
  pgss.shared_blks_written,
  pgss.local_blks_hit,
  pgss.local_blks_read,
  pgss.local_blks_dirtied,
  pgss.local_blks_written,
  pgss.temp_blks_read,
  pgss.temp_blks_written,
  pgss.blk_read_time,
  pgss.blk_write_time
FROM pg_stat_statements pgss
JOIN pg_authid ON pgss.userid = pg_authid.oid
JOIN pg_database ON pgss.dbid = pg_database.oid
"""


@routes.get(b"/", check_key=True)
def get_statements(http_context, app):
    """Return a snapshot of latest statistics of executed SQL statements and
    reset gathered statistics.
    """
    config = app.config
    dbname = config.statements.dbname
    assert dbname == "postgres", dbname
    conn = connector(
        config.postgresql.host,
        config.postgresql.port,
        config.postgresql.user,
        config.postgresql.password,
        dbname,
    )
    snapshot_datetime = now()
    try:
        conn.connect()
        conn.execute(query)
        data = list(conn.get_rows())
        conn.execute("SELECT pg_stat_statements_reset()")
    except error as e:
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
        raise HTTPError(500, "Internal server error")
    else:
        return {"snapshot_datetime": snapshot_datetime, "data": data}


class StatementsPlugin(object):
    PG_MIN_VERSION = 90500
    s = "statements"
    option_specs = [OptionSpec(s, "dbname", default="postgres")]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def load(self):
        pg_version = self.app.postgres.fetch_version()
        if pg_version < self.PG_MIN_VERSION:
            msg = "%s is incompatible with Postgres below 9.5" % (
                self.__class__.__name__)
            raise UserError(msg)

        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.option_specs)
