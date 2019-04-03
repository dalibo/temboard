# coding: utf-8

from __future__ import unicode_literals

from .spc import connector
from .spc import error as PostgresError
from .errors import UserError


class ConnectionManager(object):
    def __init__(self, postgres):
        self.postgres = postgres

    def __enter__(self):
        self.conn = connector(
            host=self.postgres.host,
            port=self.postgres.port,
            user=self.postgres.user,
            password=self.postgres.password,
            database=self.postgres.dbname
        )
        try:
            self.conn.connect()
        except PostgresError as e:
            raise UserError("Failed to connect to Postgres: %s" % e.message)
        return self.conn

    def __exit__(self, *a):
        self.conn.close()


class Postgres(object):
    def __init__(
            self, host=None, port=5432, user=None, password=None, dbname=None,
            **kw):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname
        self._server_version = None

    def __repr__(self):
        return '<%s on %s@%s:%s/%s>' % (
            self.__class__.__name__,
            self.user, self.host, self.port, self.dbname,
        )

    def connect(self):
        return ConnectionManager(self)

    def fetch_version(self):
        if self._server_version is None:
            with self.connect() as conn:
                self._server_version = conn.get_pg_version()
        return self._server_version
