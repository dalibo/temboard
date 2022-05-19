import json
from multiprocessing import Process
import time

from psycopg2 import OperationalError
from urllib.request import HTTPError

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
