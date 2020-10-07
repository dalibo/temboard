# coding: utf-8

from __future__ import unicode_literals

import re
from textwrap import dedent

import psycopg2.extensions
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from .errors import UserError
from .toolkit.pycompat import PY2


# See https://www.psycopg.org/docs/faq.html#faq-float
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    b'DEC2FLOAT' if PY2 else 'DEC2FLOAT',
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
            for row in cur:
                yield row

    def queryone(self, query, vars=None):
        with self.cursor() as cur:
            cur.execute(dedent(query), vars)
            return cur.fetchone()

    def query_scalar(self, query, vars=None):
        return next(iter(self.queryone(query, vars).values()))


class ConnectionManager(object):
    def __init__(self, postgres, app):
        self.postgres = postgres
        self.app = app

    def __enter__(self):
        try:
            self.conn = connect(
                host=self.postgres.host,
                port=self.postgres.port,
                user=self.postgres.user,
                password=self.postgres.password,
                database=self.postgres.dbname,
                connection_factory=ConnectionHelper,
                cursor_factory=RealDictCursor,
            )
            self.conn.set_session(autocommit=True)
            if self.app is not None:
                self.app.check_compatibility(self.conn.server_version)
        except Exception as e:
            raise UserError("Failed to connect to Postgres: %s" % e)
        return self.conn

    def __exit__(self, *a):
        self.conn.close()


class Postgres(object):
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
        return '<%s on %s@%s:%s/%s>' % (
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
