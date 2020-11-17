# coding: utf-8

import json
import os
import sqlite3
from textwrap import dedent
from temboardagent.tools import JSONEncoder


def bootstrap(path, dbname):
    """Create SQLite3 database model to history collected data for the
    dashboard.

    To be representative of the very recent server activity, dashboard data
    history should not contain old data, that's why the table is dropped and
    recreated when the agent starts.

    We do not need to keep in the history a lot of data (150 records by
    default) and want it to act as a FIFO queue.
    """

    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS metrics")
        c.execute(
            dedent("""
                CREATE TABLE metrics (
                    time REAL PRIMARY KEY,
                    data TEXT
                )
            """)
        )


def add_metric(path, dbname, time, data, keep_limit):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO metrics VALUES(?, ?)",
            (time, json.dumps(data, cls=JSONEncoder))
        )
        # Purge
        c.execute(
            dedent("""
                DELETE FROM metrics
                WHERE time NOT IN (
                    SELECT time FROM metrics ORDER BY time DESC
                    LIMIT ?
                )
            """),
            (keep_limit,)
        )


def get_last_metric(path, dbname):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT data FROM metrics ORDER BY time DESC LIMIT 1"
        )
        return c.fetchone()


def get_all_metrics(path, dbname):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT data FROM metrics ORDER BY time ASC"
        )
        return c.fetchall()
