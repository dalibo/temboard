import json
from multiprocessing import Process
import time

from psycopg2 import OperationalError
try:
    from urllib.request import HTTPError
except ImportError:
    from urllib2 import HTTPError

from .test.temboard import temboard_request
from .conftest import ENV, pgconnect

XSESSION = ''


def pg_sleep(duration=1):
    """
    Start a new PG connection and run pg_sleep()
    """
    with pgconnect() as conn:
        try:
            conn.execute("SELECT pg_sleep(%s)", (duration,))
        except OperationalError:
            pass  # Accept being killed


def create_database(dbname):
    """
    Create a database.
    """
    with pgconnect() as conn:
        cur = conn.cursor()
        cur.execute("CREATE DATABASE %s" % dbname)


def create_table(dbname, tablename):
    """
    Create a table and insert 5 rows in it.
    """
    with pgconnect(dbname=dbname) as conn:
        conn.execute("CREATE TABLE {} (id INTEGER)".format(tablename))
        conn.execute("INSERT INTO %s SELECT generate_series(1, 5)"
                     % (tablename,))


def lock_table_exclusive(dbname, tablename, duration):
    """
    Lock a table in exclusive mode for a while (duration in seconds).
    """
    with pgconnect(dbname=dbname) as conn:
        conn.execute("BEGIN")
        conn.execute("LOCK TABLE %s IN EXCLUSIVE MODE" % (tablename))
        time.sleep(float(duration))
        conn.execute("ROLLBACK")


def update_rows(dbname, tablename):
    """
    Update all rows of a table.
    """
    with pgconnect(dbname=dbname) as conn:
        conn.execute("UPDATE %s SET id = id + 1" % (tablename))


class TestActivity:
    def _exec_query(self, dbname, query):
        with pgconnect(dbname=dbname) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()

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
        with pgconnect():
            pass

        global XSESSION
        XSESSION = self._temboard_login()

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
        assert type(dict_data['rows'][0]['database']) == str
        assert type(dict_data['rows'][0]['user']) == str
        # can be float or 'N/A'
        assert type(dict_data['rows'][0]['cpu']) in (float, str)
        assert type(dict_data['rows'][0]['memory']) == float
        assert type(dict_data['rows'][0]['read_s']) == str
        assert type(dict_data['rows'][0]['write_s']) == str
        assert type(dict_data['rows'][0]['iow']) == str
        assert type(dict_data['rows'][0]['wait']) == str
        assert type(dict_data['rows'][0]['duration']) in (float, int)
        assert type(dict_data['rows'][0]['state']) in (str, type(None))
        assert type(dict_data['rows'][0]['query']) in (str, type(None))

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
                             r"WHERE query LIKE 'SELECT pg\_sleep%'")
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
        assert type(dict_data['rows'][0]['database']) == str
        assert type(dict_data['rows'][0]['user']) == str
        assert type(dict_data['rows'][0]['cpu']) in (float, str)
        assert type(dict_data['rows'][0]['memory']) == float
        assert type(dict_data['rows'][0]['read_s']) == str
        assert type(dict_data['rows'][0]['write_s']) == str
        assert type(dict_data['rows'][0]['iow']) == str
        assert type(dict_data['rows'][0]['relation']) == str
        assert type(dict_data['rows'][0]['type']) == str
        assert dict_data['rows'][0]['type'] == 'relation'
        assert type(dict_data['rows'][0]['mode']) == str
        assert dict_data['rows'][0]['mode'] == 'RowExclusiveLock'
        assert type(dict_data['rows'][0]['duration']) in (float, int)
        assert type(dict_data['rows'][0]['state']) in (str, type(None))
        assert type(dict_data['rows'][0]['query']) in (str, type(None))

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
        assert type(dict_data['rows'][0]['database']) == str
        assert type(dict_data['rows'][0]['user']) == str
        assert type(dict_data['rows'][0]['cpu']) in (float, str)
        assert type(dict_data['rows'][0]['memory']) == float
        assert type(dict_data['rows'][0]['read_s']) == str
        assert type(dict_data['rows'][0]['write_s']) == str
        assert type(dict_data['rows'][0]['iow']) == str
        assert type(dict_data['rows'][0]['relation']) == str
        assert type(dict_data['rows'][0]['type']) == str
        assert dict_data['rows'][0]['type'] == 'relation'
        assert type(dict_data['rows'][0]['mode']) == str
        assert dict_data['rows'][0]['mode'] == 'ExclusiveLock'
        assert type(dict_data['rows'][0]['duration']) in (float, int)
        assert type(dict_data['rows'][0]['state']) in (str, type(None))
        assert type(dict_data['rows'][0]['query']) in (str, type(None))
