# coding: utf-8

from datetime import datetime
import json
import logging
import sqlite3
from textwrap import dedent

from ..taskmanager import Task
from ..errors import StorageEngineError

logger = logging.getLogger(__name__)


def epoch_to_datetime(epoch):
    if epoch:
        return datetime.utcfromtimestamp(epoch)


def datetime_to_epoch(timestamp):
    if timestamp:
        return int((timestamp - datetime(1970, 1, 1)).total_seconds())
    return 0


class TaskListSQLite3Engine(object):
    """SQLite3 storage engine for task list management."""

    def __init__(self, dbpath):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(self.dbpath)

    def bootstrap(self):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute("PRAGMA synchronous = 1")
                c.execute(
                    dedent("""
                        CREATE TABLE IF NOT EXISTS tasks (
                            id TEXT PRIMARY KEY,
                            worker_name TEXT,
                            start_datetime BIGINT,
                            stop_datetime BIGINT,
                            status SMALLINT,
                            output TEXT,
                            options TEXT,
                            redo_interval INTEGER DEFAULT 0 NOT NULL,
                            expire INTEGER DEFAULT 0 NOT NULL
                        )
                    """)
                )
        except sqlite3.OperationalError as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not bootstrap storage engine.")

    def insert(self, task):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        task.id,
                        task.worker_name,
                        datetime_to_epoch(task.start_datetime),
                        datetime_to_epoch(task.stop_datetime),
                        task.status,
                        str(task.output) if task.output else None,
                        json.dumps(task.options),
                        task.redo_interval or 0,
                        task.expire or 0
                    )
                )
        except sqlite3.IntegrityError:
            raise KeyError("Task with id=%s already exists" % task.id)
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not insert task.")

    def update(self, task):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    dedent("""
                        UPDATE tasks
                        SET
                          worker_name = ?,
                          start_datetime = ?,
                          stop_datetime = ?,
                          status = ?,
                          output = ?,
                          options = ?,
                          redo_interval = ?,
                          expire = ?
                        WHERE id = ?
                    """),
                    (
                        task.worker_name,
                        datetime_to_epoch(task.start_datetime),
                        datetime_to_epoch(task.stop_datetime),
                        task.status,
                        str(task.output) if task.output else None,
                        json.dumps(task.options),
                        task.redo_interval or 0,
                        task.expire or 0,
                        task.id
                    )
                )
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not update task.")

    def delete(self, id):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    "DELETE FROM tasks WHERE id = ?",
                    (id,)
                )
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not delete task with id=%s" % id)

    def get(self, id):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    dedent("""
                        SELECT
                            id, worker_name, start_datetime, stop_datetime,
                            status, output, options, redo_interval, expire
                        FROM tasks
                        WHERE id = ?
                    """),
                    (id,)
                )
                r = c.fetchone()
                if not r:
                    return

                try:
                    options = json.loads(r[6])
                except ValueError as e:
                    logger.exception(str(e))
                    logger.debug(r)
                    raise StorageEngineError("Could not decode task options.")

                return Task(
                    id=r[0],
                    worker_name=r[1],
                    start_datetime=epoch_to_datetime(r[2]),
                    stop_datetime=epoch_to_datetime(r[3]),
                    status=r[4],
                    output=r[5],
                    options=options,
                    redo_interval=r[7],
                    expire=r[8]
                )

        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not get task with id=%s" % id)

    def list(self):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    dedent("""
                        SELECT
                            id, worker_name, start_datetime, stop_datetime,
                            status, output, options, redo_interval, expire
                        FROM tasks
                        ORDER BY start_datetime ASC
                    """)
                )
                for r in c.fetchall():

                    try:
                        options = json.loads(r[6])
                    except ValueError as e:
                        logger.exception(str(e))
                        logger.error("Could not convert row to Task.")
                        logger.debug(r)
                        continue

                    yield Task(
                        id=r[0],
                        worker_name=r[1],
                        start_datetime=epoch_to_datetime(r[2]),
                        stop_datetime=epoch_to_datetime(r[3]),
                        status=r[4],
                        output=r[5],
                        options=options,
                        redo_interval=r[7],
                        expire=r[8]
                    )

        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not get task list.")

    def exists(self, id):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute("SELECT 1 FROM tasks WHERE id = ?", (id,))
                return (c.fetchone() is not None)
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError(
                "Could not check that task with id=%s exists" % id
            )

    def count_by_status(self, status):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    "SELECT COUNT(id) FROM tasks WHERE status & ?",
                    (status,)
                )
                return c.fetchone()[0]
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError(
                "Could not count tasks with status & %s" % status
            )

    def recover(self, st_doing, st_aborted, st_scheduled, st_default, now):
        try:
            with self.conn:
                c = self.conn.cursor()
                # Flag ongoing task as aborted
                c.execute(
                    dedent("""
                        UPDATE tasks SET status = ?, stop_datetime = ?
                        WHERE status & ?
                    """),
                    (st_aborted, datetime_to_epoch(now), st_doing)
                )
                # Reset scheduled task to default
                c.execute(
                    "UPDATE tasks SET status = ? WHERE status & ?",
                    (st_default, st_scheduled)
                )
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not recover tasks.")

    def list_to_do(self, status, now, redo=False):
        query = dedent("""
                SELECT
                    id, worker_name, start_datetime, stop_datetime,
                    status, output, options, redo_interval, expire
                FROM tasks
                WHERE
        """)
        if redo:
            query += dedent("""
                    redo_interval > 0
                    AND (start_datetime + redo_interval) < ?
                    AND status & ?
            """)
        else:
            query += dedent("""
                    start_datetime < ?
                    AND status & ?
            """)

        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(query, (datetime_to_epoch(now), status,))
                for r in c.fetchall():

                    try:
                        options = json.loads(r[6])
                    except ValueError as e:
                        logger.exception(str(e))
                        logger.error("Could not convert row to Task.")
                        logger.debug(r)
                        continue

                    yield Task(
                        id=r[0],
                        worker_name=r[1],
                        start_datetime=epoch_to_datetime(r[2]),
                        stop_datetime=epoch_to_datetime(r[3]),
                        status=r[4],
                        output=r[5],
                        options=options,
                        redo_interval=r[7],
                        expire=r[8]
                    )

        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not get task list.")

    def purge(self, status, now):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute(
                    dedent("""
                    DELETE FROM tasks
                    WHERE
                        redo_interval = 0
                        AND (stop_datetime + expire) < ?
                        AND status & ?
                    """),
                    (datetime_to_epoch(now), status)
                )
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not purge task list.")

    def vacuum(self):
        try:
            with self.conn:
                c = self.conn.cursor()
                c.execute("VACUUM")
        except sqlite3.Error as e:
            logger.exception(str(e))
            raise StorageEngineError("Could not vacuum the database.")
