import json
import time
import os
import sys

from urllib2 import HTTPError
from test.temboard import init_env, drop_env, temboard_request

# Import spc
tbda_dir = os.path.realpath(
            os.path.join(__file__, '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)


from temboardagent.spc import connector, error  # noqa

ENV = {}
XSESSION = ''


class TestAdministration:

    @classmethod
    def setup_class(cls):
        global ENV
        ENV = init_env()

    @classmethod
    def teardown_class(cls):
        drop_env(ENV)

    def _create_dummy_db(self, dbname):
        conn = connector(
            host=ENV['pg']['socket_dir'],
            port=ENV['pg']['port'],
            user=ENV['pg']['user'],
            password=ENV['pg']['password'],
            database='postgres'
        )
        conn.connect()
        conn.execute("CREATE DATABASE %s" % (dbname))
        conn.close()

    def _drop_dummy_db(self, dbname):
        conn = connector(
            host=ENV['pg']['socket_dir'],
            port=ENV['pg']['port'],
            user=ENV['pg']['user'],
            password=ENV['pg']['password'],
            database='postgres'
        )
        conn.connect()
        conn.execute("DROP DATABASE %s" % (dbname))
        conn.close()

    def _create_dummy_table(self, dbname, tablename):
        conn = connector(
            host=ENV['pg']['socket_dir'],
            port=ENV['pg']['port'],
            user=ENV['pg']['user'],
            password=ENV['pg']['password'],
            database=dbname
        )
        conn.connect()
        conn.execute("CREATE TABLE %s (id INTEGER)" % (tablename))
        conn.execute("INSERT INTO %s SELECT generate_series(1, 500000)" % (
                        tablename
                        ))
        conn.close()

    def _get_duration_since_last_vacuum(self, dbname, tablename):
        conn = connector(
            host=ENV['pg']['socket_dir'],
            port=ENV['pg']['port'],
            user=ENV['pg']['user'],
            password=ENV['pg']['password'],
            database=dbname
        )
        conn.connect()
        query = """
SELECT
    coalesce(EXTRACT(EPOCH FROM (NOW() - last_vacuum)),0) AS duration
FROM
    pg_stat_user_tables
WHERE
    relname = '%s'""" % (
            tablename
            )
        conn.execute(query)
        conn.close()
        return list(conn.get_rows())[0]['duration']

    def _temboard_login(self):
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/login' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={"Content-type": "application/json"},
                data={
                    'username': ENV['agent']['user'],
                    'password': ENV['agent']['password']
                    }
                )
        return json.loads(res)['session']

    def test_00_env_pg(self):
        """
        [administration] 00: PostgreSQL instance is up & running
        """
        conn = connector(
            host=ENV['pg']['socket_dir'],
            port=ENV['pg']['port'],
            user=ENV['pg']['user'],
            password=ENV['pg']['password'],
            database='postgres'
        )
        try:
            conn.connect()
            conn.close()
            global XSESSION
            XSESSION = self._temboard_login()
            assert True
        except error:
            assert False

    def test_01_vacuum_ok(self):
        """
        [administration] 01: POST /administration/vacuum : Schedule & run a VACUUM on a table
        """  # noqa
        dummy_dbname = 'test_temboard'
        dummy_tablename = 'test_vacuum'

        self._create_dummy_db(dummy_dbname)
        self._create_dummy_table(dummy_dbname, dummy_tablename)

        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/administration/vacuum' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                    ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            },
            data={
                "database": dummy_dbname,
                "table": dummy_tablename,
                "mode": "standard"
            }
        )

        if status != 200:
            self._drop_dummy_db(dummy_dbname)
            assert False
        else:
            time.sleep(2)
            if self._get_duration_since_last_vacuum(
                    dummy_dbname, dummy_tablename) > 0:
                self._drop_dummy_db(dummy_dbname)
                assert True
            else:
                self._drop_dummy_db(dummy_dbname)
                assert False

    def test_02_vacuum_uniqness(self):
        """
        [administration] 02: POST /administration/vacuum : Schedule & run 2 VACUUM orders on the same table, getting a 402 error is expected on the 2nd call
        """  # noqa
        dummy_dbname = 'test_temboard02'
        dummy_tablename = 'test_vacuum02'

        self._create_dummy_db(dummy_dbname)
        self._create_dummy_table(dummy_dbname, dummy_tablename)
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/administration/vacuum' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                        ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    "database": dummy_dbname,
                    "table": dummy_tablename,
                    "mode": "standard"
                }
            )
        except HTTPError as e:
            status = e.code
        if status != 200:
            self._drop_dummy_db(dummy_dbname)
            assert False
        else:
            status = 0
            try:
                (status, res) = temboard_request(
                    ENV['agent']['ssl_cert_file'],
                    method='POST',
                    url='https://%s:%s/administration/vacuum' % (
                            ENV['agent']['host'],
                            ENV['agent']['port']
                            ),
                    headers={
                        "Content-type": "application/json",
                        "X-Session": XSESSION
                    },
                    data={
                        "database": dummy_dbname,
                        "table": dummy_tablename,
                        "mode": "standard"
                    }
                )
            except HTTPError as e:
                status = e.code
            self._drop_dummy_db(dummy_dbname)
            assert status == 402

    def test_03_command_status(self):
        """
        [administration] 03: GET /command/<cid> : Schedule a VACUUM order, and check status
        """  # noqa
        dummy_dbname = 'test_temboard'
        dummy_tablename = 'test_vacuum'

        self._create_dummy_db(dummy_dbname)
        self._create_dummy_table(dummy_dbname, dummy_tablename)
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/administration/vacuum' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                        ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    "database": dummy_dbname,
                    "table": dummy_tablename,
                    "mode": "standard"
                }
            )
        except HTTPError as e:
            status = e.code

        if status != 200:
            self._drop_dummy_db(dummy_dbname)
            assert False
        # First call to /command/<cid>, command's state must be set to 0
        # (work's not been started yet), or 1 (work's been started)
        cid = json.loads(res)['cid']
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/command/%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        cid
                        ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code

        if status != 200:
            self._drop_dummy_db(dummy_dbname)
            assert False
        d_data = json.loads(res)
        if d_data['state'] != 0 and d_data['state'] != 1:
            self._drop_dummy_db(dummy_dbname)
            assert False
        # Sleep for 5 seconds, after that vacuum worker should be done.
        time.sleep(5)
        # Then let do a 2nd call, command's state must be set to 2
        # (COMMAND_DONE)
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/command/%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        cid
                        ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        if status != 200:
            self._drop_dummy_db(dummy_dbname)
            assert False
        d_data = json.loads(res)
        if d_data['state'] != 2:
            self._drop_dummy_db(dummy_dbname)
            assert False
        # On this last call, command status shouldn't be returned
        # because the command has been removed after the last call to the API
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/command/%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        cid
                        ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        self._drop_dummy_db(dummy_dbname)
        assert status == 401
