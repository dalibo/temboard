import logging
import sys
from argparse import (
    ArgumentParser,
    SUPPRESS as UNDEFINED_ARGUMENT,
)

import alembic.command
import alembic.config
import sqlalchemy.exc

from .__main__ import VersionAction, map_pgvars, TemboardApplication
from .model import build_alembic_config, check_schema
from .toolkit import validators as v
from .toolkit.app import (
    define_core_arguments,
)
from .toolkit.configuration import OptionSpec
from .toolkit.errors import UserError


logger = logging.getLogger(__name__)


class MigrateDBApplication(TemboardApplication):
    PROGRAM = 'temboard-migratedb'

    def main(self, argv, environ):
        parser = ArgumentParser(
            prog=self.PROGRAM,
            description="temBoard schema migrator.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_arguments(parser)
        args = parser.parse_args(argv)
        environ = map_pgvars(environ)
        self.bootstrap(args=args, environ=environ)

        self.log_versions()

        if args.command is None:
            raise UserError("Missing sub-command. See --help")

        command_method = 'command_' + args.command
        try:
            command = getattr(self, command_method)
        except AttributeError:
            raise UserError("Unknown command %s." % args.command)

        try:
            command(args)
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
