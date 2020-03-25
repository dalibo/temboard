import logging
import sys
from time import sleep

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine


Session = sessionmaker()
logger = logging.getLogger(__name__)


def format_dsn(dsn):
    fmt = "postgresql://{user}:{password}@:{port}/{dbname}?host={host}"
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
    for i in range(10):
        try:
            engine.connect().close()
            break
        except Exception as e:
            if i == 9:
                raise
            logger.warn("Failed to connect to database: %s", e)
            logger.info("Retrying in %ss.", i)
            sleep(i)
