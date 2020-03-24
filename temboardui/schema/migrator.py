import os
from glob import glob
from textwrap import dedent

from psycopg2 import ProgrammingError
from psycopg2.errorcodes import UNDEFINED_TABLE


class Migrator(object):
    versionsdir = os.path.dirname(__file__) + '/versions'

    def __init__(self):
        self.current_version = None
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

    def inspect_current_version(self, conn):
        try:
            with conn.cursor() as cur:
                cur.execute(dedent("""\
                SELECT version
                FROM application.schema_migration_log
                ORDER BY version DESC
                LIMIT 1;
                """))
                row = cur.fetchone()
            self.current_version = row[0]
        except ProgrammingError as e:
            # None is for unit tests.
            if e.pgcode in (None, UNDEFINED_TABLE):
                pass
            else:
                raise
        finally:
            conn.rollback()
        return self.current_version

    def inspect_available_versions(self):
        self.versions = sorted([
            os.path.basename(f)
            for f in glob(self.versionsdir + "/*.sql")
        ])

    def apply(self, conn, version):
        path = os.path.join(self.versionsdir, version)
        with open(path) as fo:
            sql = fo.read()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(dedent("""\
                INSERT INTO application.schema_migration_log
                (version)
                VALUES (%s);
                """), (version,))
