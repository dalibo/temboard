import logging
import sys

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine

from ..utils import check_sqlalchemy_connectivity

Session = sessionmaker()
logger = logging.getLogger(__name__)


def configure(dsn, **kwargs):
    if hasattr(dsn, 'items'):
        fmt = "postgresql://{user}:{password}@:{port}/{dbname}?host={host}"
        dsn = fmt.format(**dsn)

    try:
        engine = create_engine(dsn)
        check_sqlalchemy_connectivity(engine)
    except Exception as e:
        logger.warning("Connection to the database failed: %s", e)
        logger.warning("Please check your configuration.")
        sys.stderr.write("FATAL: %s\n" % e.message)
        exit(10)
    Session.configure(bind=engine, **kwargs)

    # For legacy purpose, we return engine to ease binding other Session maker
    # with the same engine.
    return engine
