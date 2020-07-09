import json
import os
import sys
from multiprocessing import Process
import time

try:
    from urllib.request import HTTPError
except ImportError:
    from urllib2 import HTTPError

from test.temboard import temboard_request
from conftest import ENV

# Import spc
tbda_dir = os.path.realpath(os.path.join(__file__, '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa

XSESSION = ''


def pg_sleep(duration=1):
    """
    Start a new PG connection and run pg_sleep()
    """
    conn = connector(host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
                     user=ENV['pg']['user'], password=ENV['pg']['password'],
                     database='postgres')
    try:
        conn.connect()
        conn.execute("SELECT pg_sleep(%s)" % (duration))
        conn.close()
    except error:
        pass


def create_database(dbname):
    """
    Create a database.
    """
    conn = connector(host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
                     user=ENV['pg']['user'], password=ENV['pg']['password'],
                     database='postgres')
    try:
        conn.connect()
        conn.execute("CREATE DATABASE %s" % (dbname))
        conn.close()
    except error:
        pass


def create_table(dbname, tablename):
    """
    Create a table and insert 5 rows in it.
    """
    conn = connector(host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
                     user=ENV['pg']['user'], password=ENV['pg']['password'],
                     database=dbname)
    try:
        conn.connect()
        conn.execute("CREATE TABLE %s (id INTEGER)" % (tablename))
        conn.execute("INSERT INTO %s SELECT generate_series(1, 5)"
                     % (tablename))
        conn.close()
    except error:
        pass


def lock_table_exclusive(dbname, tablename, duration):
    """
    Lock a table in exclusive mode for a while (duration in seconds).
    """
    conn = connector(host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
                     user=ENV['pg']['user'], password=ENV['pg']['password'],
                     database=dbname)
    try:
        conn.connect()
        conn.execute("BEGIN")
        conn.execute("LOCK TABLE %s IN EXCLUSIVE MODE" % (tablename))
        time.sleep(float(duration))
        conn.execute("ROLLBACK")
        conn.close()
    except error:
        pass


def update_rows(dbname, tablename):
    """
    Update all rows of a table.
    """
    conn = connector(host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
                     user=ENV['pg']['user'], password=ENV['pg']['password'],
                     database=dbname)
    try:
        conn.connect()
        conn.execute("UPDATE %s SET id = id + 1" % (tablename))
        conn.close()
    except error:
        pass


class TestActivity:
    def _exec_query(self, dbname, query):
        conn = connector(host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
                         user=ENV['pg']['user'],
                         password=ENV['pg']['password'], database=dbname)
        conn.connect()
        conn.execute(query)
        conn.close()
        return list(conn.get_rows())

    def _temboard_login(self):
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/login'
            % (ENV['agent']['host'], ENV['agent']['port']),
            headers={"Content-type": "application/json"},
            data={
                'username': ENV['agent']['user'],
                'password': ENV['agent']['password']
            }
        )
        return json.loads(res)['session']

    def test_00_env_pg(self):
        """
        [activity] 00: PostgreSQL instance is up & running
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

    def test_01_activity_root(self):
        """
        [activity] 01: GET /activity : Check HTTP code (200) and the whole data structure
        """  # noqa

        # Start a long query in a dedicated process.
        p = Process(target=pg_sleep, args=(1,))
        p.start()

        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/activity'
                % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        dict_data = json.loads(res)

        # Join the process
        p.join()

        assert status == 200
        assert 'rows' in dict_data
        assert type(dict_data['rows']) == list
        assert type(dict_data['rows'][0]) == dict
        assert 'pid' in dict_data['rows'][0]
        assert 'database' in dict_data['rows'][0]
        assert 'user' in dict_data['rows'][0]
        assert 'client' in dict_data['rows'][0]
        assert 'cpu' in dict_data['rows'][0]
        assert 'memory' in dict_data['rows'][0]
        assert 'read_s' in dict_data['rows'][0]
        assert 'write_s' in dict_data['rows'][0]
        assert 'iow' in dict_data['rows'][0]
        assert 'wait' in dict_data['rows'][0]
        assert 'duration' in dict_data['rows'][0]
        assert 'state' in dict_data['rows'][0]
        assert 'query' in dict_data['rows'][0]
        assert type(dict_data['rows'][0]['pid']) == int
        assert type(dict_data['rows'][0]['database']) == unicode
        assert type(dict_data['rows'][0]['user']) == unicode
        # can be float or 'N/A'
        assert type(dict_data['rows'][0]['cpu']) in (float, unicode)
        assert type(dict_data['rows'][0]['memory']) == float
        assert type(dict_data['rows'][0]['read_s']) == unicode
        assert type(dict_data['rows'][0]['write_s']) == unicode
        assert type(dict_data['rows'][0]['iow']) == unicode
        assert type(dict_data['rows'][0]['wait']) == unicode
        assert type(dict_data['rows'][0]['duration']) in (float, int)
        assert type(dict_data['rows'][0]['state']) in (unicode, type(None))
        assert type(dict_data['rows'][0]['query']) in (unicode, type(None))

    def test_02_activity_kill(self):
        """
        [activity] 02: POST /activity/kill : Test backend termination
        """  # noqa

        # Start a very long query in a dedicated process.
        p = Process(target=pg_sleep, args=(3,))
        p.start()

        # Sleep a while before inspecting pg_stat_activity...
        time.sleep(1)

        # Get the pid of the backend running the long query
        r = self._exec_query('postgres',
                             "SELECT pid FROM pg_stat_activity "
                             "WHERE query LIKE 'SELECT pg\_sleep%'")
        backend_pid = r[0]['pid']

        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/activity/kill'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    "pids": [backend_pid]
                }
            )
        except HTTPError as e:
            status = e.code
        dict_data = json.loads(res)

        # Join the process
        p.join()

        assert status == 200
        assert 'backends' in dict_data
        assert type(dict_data['backends']) == list
        assert type(dict_data['backends'][0]) == dict
        assert 'pid' in dict_data['backends'][0]
        assert 'killed' in dict_data['backends'][0]
        assert type(dict_data['backends'][0]['pid']) == int
        assert type(dict_data['backends'][0]['killed']) == bool
        assert dict_data['backends'][0]['pid'] == backend_pid

    def test_03_activity_waiting(self):
        """
        [activity] 03: GET /activity/waiting : Check HTTP code (200) and the whole data structure
        """  # noqa

        # Create a new DB
        dbname = 'testdbw'
        tablename = 'testtablew'
        create_database(dbname)
        create_table(dbname, tablename)
        # Lock table in exclusive mode in a dedicated process for 5 seconds.
        p1 = Process(target=lock_table_exclusive, args=(dbname, tablename, 5))
        p1.start()
        # Sleep a bit
        time.sleep(1)
        # Try to update rows from the locked table
        p2 = Process(target=update_rows, args=(dbname, tablename))
        p2.start()

        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/activity/waiting'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        dict_data = json.loads(res)

        # Join the process
        p1.join()
        p2.join()

        assert status == 200
        assert 'rows' in dict_data
        assert type(dict_data['rows']) == list
        # One row is expected
        assert len(dict_data['rows']) == 1
        assert type(dict_data['rows'][0]) == dict
        assert 'pid' in dict_data['rows'][0]
        assert 'database' in dict_data['rows'][0]
        assert 'user' in dict_data['rows'][0]
        assert 'cpu' in dict_data['rows'][0]
        assert 'memory' in dict_data['rows'][0]
        assert 'read_s' in dict_data['rows'][0]
        assert 'write_s' in dict_data['rows'][0]
        assert 'iow' in dict_data['rows'][0]
        assert 'relation' in dict_data['rows'][0]
        assert 'type' in dict_data['rows'][0]
        assert 'mode' in dict_data['rows'][0]
        assert 'duration' in dict_data['rows'][0]
        assert 'state' in dict_data['rows'][0]
        assert 'query' in dict_data['rows'][0]
        assert type(dict_data['rows'][0]['pid']) == int
        assert type(dict_data['rows'][0]['database']) == unicode
        assert type(dict_data['rows'][0]['user']) == unicode
        assert type(dict_data['rows'][0]['cpu']) in (float, unicode)
        assert type(dict_data['rows'][0]['memory']) == float
        assert type(dict_data['rows'][0]['read_s']) == unicode
        assert type(dict_data['rows'][0]['write_s']) == unicode
        assert type(dict_data['rows'][0]['iow']) == unicode
        assert type(dict_data['rows'][0]['relation']) == unicode
        assert type(dict_data['rows'][0]['type']) == unicode
        assert dict_data['rows'][0]['type'] == u'relation'
        assert type(dict_data['rows'][0]['mode']) == unicode
        assert dict_data['rows'][0]['mode'] == u'RowExclusiveLock'
        assert type(dict_data['rows'][0]['duration']) in (float, int)
        assert type(dict_data['rows'][0]['state']) in (unicode, type(None))
        assert type(dict_data['rows'][0]['query']) in (unicode, type(None))

    def test_04_activity_blocking(self):
        """
        [activity] 04: GET /activity/blocking : Check HTTP code (200) and the whole data structure
        """  # noqa

        # Create a new DB
        dbname = 'testdbb'
        tablename = 'testtableb'
        create_database(dbname)
        create_table(dbname, tablename)
        # Lock table in exclusive mode in a dedicated process for 5 seconds.
        p1 = Process(target=lock_table_exclusive, args=(dbname, tablename, 5))
        p1.start()
        # Sleep a bit
        time.sleep(1)
        # Try to update rows from the locked table
        p2 = Process(target=update_rows, args=(dbname, tablename))
        p2.start()

        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/activity/blocking'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        dict_data = json.loads(res)

        # Join the process
        p1.join()
        p2.join()

        assert status == 200
        assert 'rows' in dict_data
        assert type(dict_data['rows']) == list
        # One row is expected
        assert len(dict_data['rows']) == 1
        assert type(dict_data['rows'][0]) == dict
        assert 'pid' in dict_data['rows'][0]
        assert 'database' in dict_data['rows'][0]
        assert 'user' in dict_data['rows'][0]
        assert 'cpu' in dict_data['rows'][0]
        assert 'memory' in dict_data['rows'][0]
        assert 'read_s' in dict_data['rows'][0]
        assert 'write_s' in dict_data['rows'][0]
        assert 'iow' in dict_data['rows'][0]
        assert 'relation' in dict_data['rows'][0]
        assert 'type' in dict_data['rows'][0]
        assert 'mode' in dict_data['rows'][0]
        assert 'duration' in dict_data['rows'][0]
        assert 'state' in dict_data['rows'][0]
        assert 'query' in dict_data['rows'][0]
        assert type(dict_data['rows'][0]['pid']) == int
        assert type(dict_data['rows'][0]['database']) == unicode
        assert type(dict_data['rows'][0]['user']) == unicode
        assert type(dict_data['rows'][0]['cpu']) in (float, unicode)
        assert type(dict_data['rows'][0]['memory']) == float
        assert type(dict_data['rows'][0]['read_s']) == unicode
        assert type(dict_data['rows'][0]['write_s']) == unicode
        assert type(dict_data['rows'][0]['iow']) == unicode
        assert type(dict_data['rows'][0]['relation']) == unicode
        assert type(dict_data['rows'][0]['type']) == unicode
        assert dict_data['rows'][0]['type'] == u'relation'
        assert type(dict_data['rows'][0]['mode']) == unicode
        assert dict_data['rows'][0]['mode'] == u'ExclusiveLock'
        assert type(dict_data['rows'][0]['duration']) in (float, int)
        assert type(dict_data['rows'][0]['state']) in (unicode, type(None))
        assert type(dict_data['rows'][0]['query']) in (unicode, type(None))
