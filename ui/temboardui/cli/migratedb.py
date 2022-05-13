import logging
from contextlib import closing

from psycopg2 import connect

from ..model import format_dsn
from ..model.migrator import Migrator
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from .app import app


logger = logging.getLogger(__name__)


@app.command
class MigrateDB(SubCommand):
    """ Manage temBoard own database. """

    def main(self, args):
        raise UserError("Missing sub-command. See --help for details.")

    def init_migrator(self):
        migrator = Migrator()
        migrator.inspect_available_versions()
        return migrator

    def make_conn(self):
        return closing(connect(format_dsn(self.app.config.repository)))


@MigrateDB.command
class Check(SubCommand):
    """Check schema synchronisation status only."""

    def main(self, args):
        migrator = self.parent.init_migrator()

        with self.parent.make_conn() as conn:
            migrator.inspect_current_version(conn)
            migrator.check()


@MigrateDB.command
class Upgrade(SubCommand):
    """Upgrade temBoard database to latest revision."""

    def main(self, args):
        migrator = self.parent.init_migrator()

        with self.parent.make_conn() as conn:
            migrator.inspect_current_version(conn)
            for version in migrator.missing_versions:
                logger.info("Upgrading database to version %s.", version)
                migrator.apply(conn, version)

        logger.info("Database up to date.")
