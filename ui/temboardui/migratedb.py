import logging
import sys
from argparse import (
    ArgumentParser,
    SUPPRESS as UNDEFINED_ARGUMENT,
)
from contextlib import closing

from psycopg2 import connect

from .__main__ import VersionAction, map_pgvars, TemboardApplication
from .model import format_dsn
from .model.migrator import Migrator
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
        self.apply_config()

        if args.command is None:
            raise UserError("Missing sub-command. See --help")

        self.migrator = Migrator()
        self.migrator.inspect_available_versions()

        command_method = 'command_' + args.command
        try:
            command = getattr(self, command_method)
        except AttributeError:
            raise UserError("Unknown command %s." % args.command)

        with closing(connect(format_dsn(self.config.repository))) as conn:
            self.migrator.inspect_current_version(conn)
            command(args, conn)

    def apply_config(self):
        # bypass TemboardApplication apply_config
        super(TemboardApplication, self).apply_config()

    def command_check(self, args, conn):
        self.migrator.check()

    def command_upgrade(self, args, conn):
        for version in self.migrator.missing_versions:
            logger.info("Upgrading database to version %s.", version)
            self.migrator.apply(conn, version)
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
