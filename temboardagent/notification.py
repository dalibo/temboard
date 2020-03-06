# coding: utf-8

from datetime import datetime
import logging
import os
import sqlite3
from textwrap import dedent
import time

from temboardagent.errors import NotificationError

logger = logging.getLogger(__name__)


class Notification(object):
    """Notifications are log messages stored in a sqlite table aimed to keep a
    track of each action impacting PostgreSQL server configuration or
    its behavior.

    For now, they are pushed when one of the following actions is triggered:
    - PostgreSQL reloaded.
    - PostgreSQL setting changed.
    - User login.
    - User session expired.
    - PostgreSQL backend termination.

    Maximum number of record is 1000, FIFO behavior is expected.
    """

    def __init__(self, username, message):

        if type(username) == bytes:
            username = username.decode('utf-8')
        if type(message) == bytes:
            message = message.decode('utf-8')

        self.time = time.time()
        self.username = username
        self.message = message


class NotificationMgmt():

    @classmethod
    def bootstrap(self, config):
        db_path = os.path.join(config.temboard.home, 'core.db')
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute(
                dedent("""
                    CREATE TABLE IF NOT EXISTS action_logs (
                        time REAL,
                        username TEXT,
                        message TEXT
                    )
                """)
            )
            c.execute(
                dedent("""
                    CREATE INDEX IF NOT EXISTS idx_action_logs_time
                    ON action_logs(time)
                """)
            )

    @classmethod
    def push(self, config, notification):
        try:

            db_path = os.path.join(config.temboard.home, 'core.db')
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO action_logs VALUES (?, ?, ?)",
                    (notification.time, notification.username,
                     notification.message)
                )
                # Purge action_logs, we want to keep only the last 100 messages
                c.execute(
                    dedent("""
                        DELETE FROM action_logs
                        WHERE time NOT IN (
                            SELECT time
                            FROM action_logs
                            ORDER BY time DESC
                            LIMIT 1000
                        )
                    """)
                )

        except sqlite3.Error as e:
            logger.exception(str(e))
            raise NotificationError('Can not push new notification')

    @classmethod
    def get_last_n(self, config, n):

        limit = " LIMIT %s" % n if int(n) > -1 else ""

        try:

            db_path = os.path.join(config.temboard.home, 'core.db')
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT time, username, message FROM action_logs "
                          "ORDER BY time DESC " + limit)
                for timestamp, username, message in c.fetchall():
                    yield dict(
                        date=datetime.utcfromtimestamp(
                            int(timestamp)
                        ).isoformat(),
                        username=username,
                        message=message
                    )

        except sqlite3.Error as e:
            logger.exception(str(e))
            raise NotificationError('Can not get last notifications')
