import logging
import sys
from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
from contextlib import closing

from psycopg2 import connect

from ..__main__ import (
    VersionAction,
    define_core_arguments,
    list_repository_specs,
)
from ..version import __version__
from ..model import format_dsn
from ..toolkit.app import BaseApplication
from ..version import inspect_versions
from .migrator import Migrator


logger = logging.getLogger('temboardui.schema.migrator')


class MigrateDBApplication(BaseApplication):
    DEFAULT_CONFIGFILE = '/etc/temboard/temboard.conf'
    PROGRAM = 'temboard-migratedb'
    REPORT_URL = "https://github.com/dalibo/temboard/issues"
    VERSION = __version__

    def main(self, argv, environ):
        parser = ArgumentParser(
            prog='temboard-migratedb',
            description="temBoard schema migrator.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_arguments(parser)
        args = parser.parse_args(argv)
        self.bootstrap(args=args, environ=environ)

        versions = inspect_versions()
        logger.info(
            "Starting temBoard migratedb %s on %s %s.",
            versions['temboard'],
            versions['distname'], versions['distversion'])
        logger.debug(
            "Using Python %s (%s).",
            versions['python'], versions['pythonbin'])
        logger.debug("Using psycopg2 %s.", versions['psycopg2'])

        migrator = Migrator()
        logger.debug("Inspecting expected schema version.")
        migrator.inspect_available_versions()
        dsn = format_dsn(self.config.repository)
        with closing(connect(dsn)) as pgconn:
            logger.debug("Connected to %s.", pgconn.dsn)
            migrator.inspect_current_version(pgconn)
            logger.info(
                "Schema version is %s.",
                migrator.current_version or "uninitialized")

            for version in migrator.missing_versions:
                logger.info("Applying %s.", version)
                migrator.apply(pgconn, version)

            logger.info("Database is up to date.")


def define_arguments(parser):
    define_core_arguments(parser)
    parser.add_argument(
        '-V', '--version',
        action=VersionAction,
        help='show version and exit',
    )


migratedb = MigrateDBApplication(
    specs=list_repository_specs(),
    with_plugins=None,
)

if '__main__' == __name__:
    sys.exit(migratedb())
