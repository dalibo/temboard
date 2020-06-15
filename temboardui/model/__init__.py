import logging
import os.path
import sys
from time import sleep

import alembic.config
import sqlalchemy.exc
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine

from ..toolkit.errors import UserError


Session = sessionmaker()
logger = logging.getLogger(__name__)


def format_dsn(dsn):
    fmt = "postgresql://{user}:{password}@:{port}/{dbname}?host={host}"
    return fmt.format(**dsn)


def build_alembic_config(temboard_config):
    config = alembic.config.Config()
    config.set_main_option(
        'sqlalchemy.url',
        format_dsn(temboard_config.repository),
    )
    config.set_main_option(
        'script_location',
        os.path.dirname(__file__) + '/alembic',
    )
    return config


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


def worker_engine(dbconf):
    """Create a new stand-alone SQLAlchemy engine to be instantiated in worker
    context.
    """
    return create_engine(format_dsn(dbconf))


def check_schema(config):
    # Derived from alembic.command.current.

    alembic_cfg = build_alembic_config(config)
    script = ScriptDirectory.from_config(alembic_cfg)

    def fn(current, context):
        target = script.get_current_head()
        current = context.get_current_revision()

        if current:
            logger.debug("temBoard database revision is %s.", current)
        else:
            logger.debug("temBoard database is uninitialized.")

        if current != target:
            raise UserError(
                "Database is not up to date. Please use temboard-migratedb."
            )
        else:
            logger.info("temBoard database is up-to-date.")

        return []  # Tells MigrationContext to skip migrations.

    with EnvironmentContext(alembic_cfg, script, fn=fn):
        try:
            script.run_env()
        except sqlalchemy.exc.OperationalError as e:
            raise UserError("Failed to check schema: %s." % e)
