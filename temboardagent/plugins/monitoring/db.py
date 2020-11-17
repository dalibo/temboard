# coding: utf-8

import json
import os
import sqlite3
from textwrap import dedent
from time import time as current_time
from temboardagent.tools import JSONEncoder


def bootstrap(path, dbname):
    """Create SQLite database model we use to store collected data.

    last_measures table aims to keep a track of the last collected values
    (for some metrics, not all) we need to have to compute delta. This table
    must be purged when the agent starts because we do not want to compute
    delta values with potentially old data resulting with outliers.

    metrics table is used to queued collected data before they are pushed to
    temboard server.
    """

    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS last_measures")
        c.execute(
            dedent("""
                CREATE TABLE last_measures (
                    time REAL,
                    key TEXT PRIMARY KEY,
                    data TEXT
                )
            """)
        )
        c.execute(
            dedent("""
                CREATE TABLE IF NOT EXISTS metrics (
                    time REAL PRIMARY KEY,
                    data TEXT
                )
            """)
        )


def add_metric(path, dbname, time, data):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO metrics VALUES(?, ?)",
            (time, json.dumps(data, cls=JSONEncoder))
        )
        # When data are pulled from temboard server, we need to keep 6 hours of
        # data history for recovery.
        time_limit = current_time() - (60 * 60 * 6)
        c.execute(
            "DELETE FROM metrics WHERE time < ?",
            (time_limit,)
        )


def delete_metric(path, dbname, time):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM metrics WHERE time = ?",
            (time,)
        )


def get_metrics(path, dbname, limit=50, start_timestamp=None):
    query = "SELECT time, data FROM metrics"
    args = ()
    if start_timestamp:
        query += " WHERE time >= ?"
        args += (start_timestamp,)
    else:
        # By default we want only the most recent record. This could be
        # achieved in a most elegant an simple way, but we want to keep the
        # same logic wheter or not start_timestamp is in use.
        query += " WHERE time >= (SELECT MAX(time) FROM metrics)"

    query += " ORDER BY time ASC"

    if limit:
        query += " LIMIT ?"
        args += (limit,)

    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(query, args)
        return c.fetchall()


def get_last_measure(path, dbname, key):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT time, data FROM last_measures WHERE key = ?",
            (key,)
        )
        return c.fetchone()


def upsert_last_measure(path, dbname, time, key, data):
    with sqlite3.connect(os.path.join(path, dbname)) as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO last_measures VALUES(?, ?, ?)",
                (time, key, json.dumps(data, cls=JSONEncoder))
            )
        except sqlite3.IntegrityError:
            c.execute(
                "UPDATE last_measures SET time = ?, data = ? "
                "WHERE key = ?",
                (time, json.dumps(data, cls=JSONEncoder), key)
            )
