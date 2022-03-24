import logging
import re
from textwrap import dedent

import psycopg2.extensions
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from .errors import UserError


logger = logging.getLogger(__name__)


# See https://www.psycopg.org/docs/faq.html#faq-float
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)


def pg_escape(in_string, escapee_char=r"'"):
    out_string = ''
    out_string += escapee_char
    out_string += re.sub(escapee_char, escapee_char * 2, in_string)
    out_string += escapee_char
    return out_string


class ConnectionHelper(connection):
    def execute(self, query, vars=None):
        with self.cursor() as cur:
            cur.execute(dedent(query), vars)

    def query(self, query, vars=None):
        with self.cursor() as cur:
            cur.execute(dedent(query), vars)
            yield from cur

    def queryone(self, query, vars=None):
        with self.cursor() as cur:
            cur.execute(dedent(query), vars)
            return cur.fetchone()

    def query_scalar(self, query, vars=None):
        row = self.queryone(query, vars)
        if row is None:
            return
        else:
            return next(iter(row.values()))


class ConnectionManager:
    def __init__(self, postgres, app):
        self.postgres = postgres
        self.app = app
        self.conn = None

    def open(self):
        logger.debug(
            "Opening Postgres connexion to database %s.",
            self.postgres.dbname)
        try:
            self.conn = connect(
                host=self.postgres.host,
                port=self.postgres.port,
                user=self.postgres.user,
                password=self.postgres.password,
                database=self.postgres.dbname,
                connection_factory=ConnectionHelper,
                cursor_factory=RealDictCursor,
                application_name='temboard-agent',
            )
            self.conn.set_session(autocommit=True)
            if self.app is not None:
                self.app.check_compatibility(self.conn.server_version)
        except Exception as e:
            raise UserError("Failed to connect to Postgres: %s" % e)
        return self.conn

    def close(self):
        logger.debug("Closing connection to %s.", self.postgres.dbname)
        self.conn.close()
        self.conn = None

    def __enter__(self):
        if self.conn is None:
            self.open()
        return self.conn

    def __exit__(self, *a):
        self.close()


class Postgres:
    def __init__(
            self, host=None, port=5432, user=None, password=None, dbname=None,
            app=None,
            **kw):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        # Compat with conninfo dict.
        if 'database' in kw:
            dbname = kw['database']
        self.dbname = dbname
        self.app = app
        self._server_version = None

    def __repr__(self):
        return '<{} on {}@{}:{}/{}>'.format(
            self.__class__.__name__,
            self.user, self.host, self.port, self.dbname,
        )

    def connect(self):
        return ConnectionManager(self, self.app)

    def fetch_version(self):
        if self._server_version is None:
            with self.connect() as conn:
                self._server_version = conn.server_version
        return self._server_version

    def copy(self, **kw):
        defaults = dict(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
            app=self.app,
        )
        kw = dict(defaults, **kw)
        return self.__class__(**kw)


class ConnectionPool:
    def __init__(self, **kw):
        if 'database' in kw:
            kw['dbname'] = kw.pop('database')
        self.conn_kw = kw
        self.pool = dict()

    def get(self, dbname=None):
        conn_kw = self.conn_kw.copy()
        if dbname:
            conn_kw['dbname'] = dbname
        dbname = conn_kw['dbname']
        try:
            return self.pool[dbname]
        except KeyError:
            conn = Postgres(**conn_kw).connect()
            return self.pool.setdefault(dbname, conn.open())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for conn in self.pool.values():
            conn.close()
        self.pool = dict()
