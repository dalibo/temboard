import logging
import os
from glob import glob
from textwrap import dedent

from .. import __version__
from ..toolkit.errors import UserError

logger = logging.getLogger(__name__)


class Migrator(object):
    versionsdir = os.path.dirname(__file__) + '/versions'
    UNDEFINED = object()
    LAST_ALEMBIC_VERSION = '005_statements.sql'

    def __init__(self):
        self.current_version = self.UNDEFINED
        self.versions = []

    @property
    def target_version(self):
        return self.versions[-1]

    @property
    def missing_versions(self):
        try:
            i = self.versions.index(self.current_version)
        except ValueError:
            return self.versions
        else:
            return self.versions[i + 1:]

    def apply(self, conn, version):
        path = os.path.join(self.versionsdir, version)
        with open(path) as fo:
            sql = fo.read()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(dedent("""\
                INSERT INTO application.schema_migration_log
                (version, comment)
                VALUES (%s, 'temBoard ' || %s);
                """), (version, __version__))

    def check(self):
        current = self.current_version
        if current is self.UNDEFINED:
            raise Exception("Unknown revision.")

        if self.missing_versions:
            logger.info("Database version is %s.", self.current_version)
            logger.info("Target version is %s.", self.target_version)
            logger.debug(
                "Database is %s version(s) behind.",
                len(self.missing_versions))
            raise UserError(
                "Database is not up to date."
                " Please upgrade with temboard migratedb."
            )
        else:
            logger.info("temBoard database is up-to-date.")

    def inspect_current_version(self, conn):
        with conn.cursor() as cur:
            cur.execute(dedent("""\
            SELECT table_name
            FROM information_schema.tables
            WHERE 'application' = table_schema
                AND table_name IN ('alembic_version', 'schema_migration_log')
            """))

            rows = cur.fetchall()

            if len(rows) > 1:
                raise Exception("Inconsistent database versionning.")
            elif not len(rows):
                logger.debug("temBoard database is uninitialized.")
                self.current_version = None
            else:
                table_name, = rows[0]

                if 'alembic_version' == table_name:
                    logger.debug("temBoard database is managed by Alembic.")
                    self.current_version = self.LAST_ALEMBIC_VERSION
                else:
                    cur.execute(dedent("""\
                    SELECT version
                    FROM application.schema_migration_log
                    ORDER BY 1 DESC
                    LIMIT 1;
                    """))
                    self.current_version, = cur.fetchone()
                logger.debug(
                    "temBoard database revision is %s.", self.current_version)
        conn.commit()
        return self.current_version

    def inspect_available_versions(self):
        self.versions = sorted([
            os.path.basename(f)
            for f in glob(self.versionsdir + "/*.sql")
        ])
