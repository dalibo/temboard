#
# Configure and extend psycopg2 for temBoard
#
# - Use float for decimal.
# - dict as default row type
# - per query row_factory
# - connection helpers to hide cursor.
#

import logging
import re
from contextlib import closing
from time import sleep

from psycopg2 import connect
from psycopg2 import Error as Psycopg2Error
from psycopg2.pool import ThreadedConnectionPool
import psycopg2.extensions


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


class Postgres:
    # main object holding Postgres parameters and methods.

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
        self.connection_lost_observers = []

    def __repr__(self):
        return '<{} on {}@{}:{}/{}>'.format(
            self.__class__.__name__,
            self.user, self.host, self.port, self.dbname,
        )

    def dbpool(self):
        return DBConnectionPool(self)

    def pool(self):
        return ConnectionPool(
            app=self.app,
            observers=self.connection_lost_observers,
            minconn=1, maxconn=2,
            **self.pqvars(),
        )

    def connect(self, database=None):
        kw = self.pqvars(database)
        return closing(retry_connect(connect, self.app, **kw))

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

    def pqvars(self, dbname=None):
        return dict(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=dbname or self.dbname,
            connection_factory=FactoryConnection,
            application_name='temboard-agent',
        )

    def notify_observers(self):
        for observer in self.connection_lost_observers:
            observer()


class DBConnectionPool:
    # Pool one connection per database.
    #
    # Not thread-safe.

    def __init__(self, postgres):
        self.postgres = postgres
        self.pool = dict()

    def getconn(self, dbname=None):
        dbname = dbname or self.postgres.dbname
        conn = self.pool.get(dbname)
        if not conn:
            logger.debug("Opening connection to db %s.", dbname)
            pqvars = self.postgres.pqvars(dbname=dbname)
            conn = retry_connect(connect, self.postgres.app, **pqvars)
            self.pool[dbname] = conn

        return conn

    def closeall(self):
        for dbname in list(self.pool):
            conn = self.pool.pop(dbname)
            logger.debug("Closing pooled connection to %s.", dbname)
            conn.close()

    def __del__(self):
        self.closeall()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closeall()


class FactoryConnection(psycopg2.extensions.connection):  # pragma: nocover
    def cursor(self, *a, **kw):
        row_factory = kw.pop('row_factory', None)
        kw['cursor_factory'] = FactoryCursor.make_factory(
            row_factory=row_factory)
        return super(FactoryConnection, self).cursor(*a, **kw)

    def execute(self, sql, *args):
        with self.cursor() as cur:
            cur.execute(sql, *args)

    def query(self, sql, *args, row_factory=None):
        with self.cursor(row_factory=row_factory) as cur:
            cur.execute(sql, *args)
            for row in cur.fetchall():
                yield row

    def queryone(self, sql, *args, row_factory=None):
        with self.cursor(row_factory=row_factory) as cur:
            cur.execute(sql, *args)
            return cur.fetchone()

    def queryscalar(self, sql, *args):
        return self.queryone(sql, *args, row_factory=scalar)


class FactoryCursor(psycopg2.extensions.cursor):  # pragma: nocover
    # Implement row_factory for psycopg2.

    @classmethod
    def make_factory(cls, row_factory=None):
        # Build a cursor_factory for psycopg2 connection.
        def factory(*a, **kw):
            kw['row_factory'] = row_factory
            return cls(*a, **kw)
        return factory

    def __init__(self, conn, name=None, row_factory=None):
        super(FactoryCursor, self).__init__(conn)
        if not row_factory:
            def row_factory(**kw):
                return kw
        self._row_factory = row_factory

    def fetchone(self):
        row = super(FactoryCursor, self).fetchone()
        kw = dict(zip([c.name for c in self.description], row))
        return self._row_factory(**kw)

    def fetchmany(self, size=None):
        for row in super(FactoryCursor, self).fetchmany(size):
            kw = dict(zip([c.name for c in self.description], row))
            yield self._row_factory(**kw)

    def fetchall(self):
        for row in super(FactoryCursor, self).fetchall():
            kw = dict(zip([c.name for c in self.description], row))
            yield self._row_factory(**kw)


def scalar(**kw):
    # Row factory for scalar.
    return next(iter(kw.values()))


class RetryManager(object):
    def __init__(self, pool):
        self.pool = pool
        self.conn = None
        self.retry = False

    def __call__(self):
        return self

    def __enter__(self):
        self.conn = self.pool.getconn()
        self.retry = False
        return self.conn

    def __exit__(self, exc_type, e, exc_tb):
        if isinstance(e, Psycopg2Error):
            if e.pgcode is None:
                logger.debug("Retrying lost connection: %s", e)
                self.pool.close_all_connections()
                self.conn = None
                self.retry = True
                return True

        # Else, just clean conn and let exception bubble.
        self.pool.putconn(self.conn)
        self.conn = None


class ConnectionPool(ThreadedConnectionPool):
    def __init__(self, app, observers=None, **kw):
        self.app = app
        self.observers = observers
        super(ConnectionPool, self).__init__(**kw)

    def _connect(self, *a, **kw):
        return retry_connect(
            super(ConnectionPool, self)._connect, self.app, *a, **kw)

    def retry_connection(self):
        # Helper to retry a code block on connection lost.
        #
        # Manage pooled connection lost. Yield a context manager for one or two
        # attempt. The first attempt uses the connection as returned by the
        # pool. The second attempt closes pool and request a fresh connection.
        #
        # for attempt in postgres.retry_connection_pool():
        #     with attempt() as conn:
        #         conn.queryscalar("SELECT 1")
        #
        manager = RetryManager(self)
        for try_ in 0, 1:
            yield manager
            if not manager.retry:
                break

    def close_all_connections(self):
        # Close all connection, keeping pool opened.
        for conn in self._pool + list(self._used.values()):
            conn.close()
            self.putconn(conn)


def retry_connect(connect, app, *a, **kw):
    # Retry 3 times, 1 second wait between each try. This allows to wait for
    # Postgres to restart, but give up to consider Postgres as unavailable.
    for wait in [1] * 3 + [0]:
        try:
            conn = connect(*a, **kw)
            if not app.status.data['postgres']['available']:
                logger.info("Recovered Postgres connexion.")
                app.postgres.notify_observers()
            app.status.data['postgres']['available'] = True
            conn.set_session(autocommit=True)
            return conn
        except Exception as e:
            app.status.data['postgres']['available'] = False
            if wait:
                logger.debug("Retrying connection open in %ss: %s", wait, e)
                sleep(wait)
            else:  # Last wait is 0. Just give up.
                raise
