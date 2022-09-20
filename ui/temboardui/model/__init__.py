from builtins import range
import logging
import sys
from time import sleep

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import __version__ as sa_version, create_engine

from .migrator import Migrator
from ..toolkit.queries import QueryFiler


Session = sessionmaker(expire_on_commit=False)
logger = logging.getLogger(__name__)
# named queries, loaded with QUERIES.load() by temboardui.__main__.
QUERIES = QueryFiler(__path__[0] + '/queries')


def format_dsn(dsn):
    fmt = (
        "postgresql://{user}:{password}@:{port}"
        "/{dbname}"
        "?host={host}&application_name=temboard"
    )
    return fmt.format(**dsn)


def configure(dsn, **kwargs):
    if hasattr(dsn, 'items'):
        dsn = format_dsn(dsn)

    try:
        engine = create_engine(dsn)
        check_connectivity(engine)
    except Exception as e:
        logger.warning("Connection to the database failed: %s", e)
        logger.warning("Please check your configuration.")
        sys.stderr.write("FATAL: %s\n" % e)
        exit(10)
    Session.configure(bind=engine, **kwargs)

    # For legacy purpose, we return engine to ease binding other Session maker
    # with the same engine.
    return engine


def check_connectivity(engine):
    for i in range(1, 10):
        try:
            # Use raw psycopg2 conn to workaround old SA bug in initialization.
            conn = engine.pool._invoke_creator()
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                pgversion, = cur.fetchone()
                logger.debug("Using PostgreSQL %s.", pgversion)
            conn.close()
            break
        except Exception as e:
            if i == 9:
                raise
            logger.warning("Failed to connect to database: %s", e)
            logger.info("Retrying in %ss.", i)
            sleep(i)

    server, pgversion, _ = pgversion.split(' ', 2)
    if '.' not in pgversion and sa_version < '1.2':
        msg = "SQLAlchemy 1.1 does not support version %s."
        raise Exception(msg % pgversion)


def worker_engine(dbconf):
    """Create a new stand-alone SQLAlchemy engine to be instantiated in worker
    context.
    """
    return create_engine(format_dsn(dbconf))


def check_schema():
    engine = Session.kw['bind']
    migrator = Migrator()
    migrator.inspect_available_versions()
    migrator.inspect_current_version(engine.raw_connection().connection)
    migrator.check()
