import logging
import sys
from argparse import (
    ArgumentParser,
    SUPPRESS as UNDEFINED_ARGUMENT,
)

import alembic.command
import alembic.config
import sqlalchemy.exc

from .__main__ import VersionAction, map_pgvars
from .model import build_alembic_config, check_schema
from .toolkit import validators as v
from .toolkit.app import (
    BaseApplication,
    define_core_arguments,
)
from .toolkit.configuration import OptionSpec
from .toolkit.errors import UserError
from .version import __version__, inspect_versions


logger = logging.getLogger(__name__)


class MigrateDBApplication(BaseApplication):
    DEFAULT_CONFIGFILES = [
        '/etc/temboard/temboard.conf',
        'temboard.conf',
    ]
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
        environ = map_pgvars(environ)
        self.bootstrap(args=args, environ=environ)

        versions = inspect_versions()
        logger.debug(
            "Using Python %s (%s).",
            versions['python'], versions['pythonbin'])
        logger.debug(
            "Using Psycopg2 %s, Alembic %s and SQLAlchemy %s",
            versions['psycopg2'], versions['alembic'], versions['sqlalchemy'],
        )

        command_method = 'command_' + args.command
        try:
            getattr(self, command_method)(args)
        except sqlalchemy.exc.OperationalError as e:
            raise UserError("Failed to query Postgres server: %s." % e)

    def command_check(self, args):
        logging.getLogger('alembic').setLevel(logging.WARN)
        check_schema(self.config)

    def command_stamp(self, args):
        logging.getLogger('alembic').setLevel(logging.WARN)
        alembic_cfg = build_alembic_config(self.config)
        alembic.command.stamp(alembic_cfg, 'head')
        logger.info("Database marked as up to date.")

    def command_upgrade(self, args):
        alembic_cfg = build_alembic_config(self.config)
        alembic.command.upgrade(alembic_cfg, 'head')
        logger.info("Database up to date.")


def define_arguments(parser):
    define_core_arguments(parser)
    parser.add_argument(
        '-V', '--version',
        action=VersionAction,
        help='show version and exit',
    )
    sub = parser.add_subparsers(
        metavar="COMMAND",
        dest="command",
        help="Operation to execute on temBoard database.")
    sub.add_parser(
        "check",
        help='Check schema synchronisation status only.'
    )
    sub.add_parser(
        "stamp",
        help="Mark database as uptodate without migrating.",
    )
    sub.add_parser(
        "upgrade",
        help="Upgrade temBoard database to latest revision.",
    )


def list_options_specs():
    s = 'repository'
    yield OptionSpec(s, 'host', default='/var/run/postgresql')
    yield OptionSpec(s, 'instance', default='main')
    yield OptionSpec(s, 'port', default=5432, validator=v.port)
    yield OptionSpec(s, 'user', default='temboard')
    yield OptionSpec(s, 'password', default='temboard')
    yield OptionSpec(s, 'dbname', default='temboard')


main = MigrateDBApplication(specs=list_options_specs(), with_plugins=None)


if __name__ == "__main__":
    sys.exit(main())
