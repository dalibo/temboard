from __future__ import absolute_import

import json
import os
import sys
import time

from .test.temboard import temboard_request
from .conftest import ENV, text_type

# Import spc
tbda_dir = os.path.realpath(os.path.join(__file__, '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa

XSESSION = ''


class TestDashboard:
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
        [dashboard] 00: PostgreSQL instance is up & running
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

    def test_01_dashboard_ok(self):
        """
        [dashboard] 01: GET /dashboard : HTTP return code is 200 and the data structure is right
        """  # noqa
        # Wait 1 second just to be sure dashboard collector ran once
        time.sleep(1)
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard'
                % (ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )

        dict_data = json.loads(res)
        assert status == 200
        assert 'active_backends' in dict_data
        assert 'max_connections' in dict_data
        assert 'loadaverage' in dict_data
        assert 'os_version' in dict_data
        assert 'linux_distribution' in dict_data
        assert 'cpu_models' in dict_data
        assert isinstance(dict_data['cpu_models'], dict)
        assert 'pg_version' in dict_data
        assert 'n_cpu' in dict_data
        assert 'hitratio' in dict_data
        assert 'databases' in dict_data
        assert 'memory' in dict_data
        assert 'hostname' in dict_data
        assert 'cpu' in dict_data
        assert 'buffers' in dict_data

    def test_02_dashboard_buffers_ok(self):
        """
        [dashboard] 02: GET /dashboard/buffers : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/buffers' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )

        dict_data = json.loads(res)
        assert status == 200 \
            and 'buffers' in dict_data \
            and 'nb' in dict_data['buffers'] \
            and type(dict_data['buffers']['nb']) == int \
            and 'time' in dict_data['buffers'] \
            and type(dict_data['buffers']['time']) == float

    def test_03_dashboard_hitratio_ok(self):
        """
        [dashboard] 03: GET /dashboard/hitratio : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/hitratio' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )

        dict_data = json.loads(res)
        assert status == 200 \
            and 'hitratio' in dict_data \
            and type(dict_data['hitratio']) == float

    def test_04_dashboard_active_backends_ok(self):
        """
        [dashboard] 04: GET /dashboard/active_backends : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/active_backends' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )

        dict_data = json.loads(res)
        assert status == 200 \
            and 'active_backends' in dict_data \
            and 'nb' in dict_data['active_backends'] \
            and type(dict_data['active_backends']['nb']) == int \
            and 'time' in dict_data['active_backends'] \
            and type(dict_data['active_backends']['time']) == float

    def test_05_dashboard_cpu_ok(self):
        """
        [dashboard] 05: GET /dashboard/cpu : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/cpu' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )

        dict_data = json.loads(res)
        assert status == 200 \
            and 'cpu' in dict_data \
            and 'iowait' in dict_data['cpu'] \
            and type(dict_data['cpu']['iowait']) == float \
            and dict_data['cpu']['iowait'] >= 0 \
            and dict_data['cpu']['iowait'] <= 100 \
            and 'idle' in dict_data['cpu'] \
            and type(dict_data['cpu']['idle']) == float \
            and dict_data['cpu']['idle'] >= 0 \
            and dict_data['cpu']['idle'] <= 100 \
            and 'steal' in dict_data['cpu'] \
            and type(dict_data['cpu']['steal']) == float \
            and dict_data['cpu']['steal'] >= 0 \
            and dict_data['cpu']['steal'] <= 100 \
            and 'user' in dict_data['cpu'] \
            and type(dict_data['cpu']['user']) == float \
            and dict_data['cpu']['user'] >= 0 \
            and dict_data['cpu']['user'] <= 100 \
            and 'system' in dict_data['cpu'] \
            and type(dict_data['cpu']['system']) == float \
            and dict_data['cpu']['system'] >= 0 \
            and dict_data['cpu']['system'] <= 100 \
            and dict_data['cpu']['iowait'] + \
                dict_data['cpu']['idle'] + \
                dict_data['cpu']['steal'] + \
                dict_data['cpu']['user'] + \
                dict_data['cpu']['system'] >= 99.5 \
            and dict_data['cpu']['iowait'] + \
                dict_data['cpu']['idle'] + \
                dict_data['cpu']['steal'] + \
                dict_data['cpu']['user'] + \
                dict_data['cpu']['system'] <= 100.5

    def test_06_dashboard_loadaverage_ok(self):
        """
        [dashboard] 06: GET /dashboard/loadaverage : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/loadaverage' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'loadaverage' in dict_data \
            and type(dict_data['loadaverage']) == float

    def test_07_dashboard_memory_ok(self):
        """
        [dashboard] 07: GET /dashboard/memory : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/memory' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'memory' in dict_data \
            and 'total' in dict_data['memory'] \
            and type(dict_data['memory']['total']) == int \
            and 'active' in dict_data['memory'] \
            and type(dict_data['memory']['active']) == float \
            and dict_data['memory']['active'] >= 0 \
            and dict_data['memory']['active'] <= 100 \
            and 'cached' in dict_data['memory'] \
            and type(dict_data['memory']['cached']) == float \
            and dict_data['memory']['cached'] >= 0 \
            and dict_data['memory']['cached'] <= 100 \
            and 'free' in dict_data['memory'] \
            and type(dict_data['memory']['free']) == float \
            and dict_data['memory']['free'] >= 0 \
            and dict_data['memory']['free'] <= 100 \
            and dict_data['memory']['active'] + \
                dict_data['memory']['cached'] + \
                dict_data['memory']['free'] >= 99.5 \
            and dict_data['memory']['active'] + \
                dict_data['memory']['cached'] + \
                dict_data['memory']['free'] <= 100.5

    def test_08_dashboard_hostname_ok(self):
        """
        [dashboard] 08: GET /dashboard/hostname : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/hostname' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'hostname' in dict_data \
            and type(dict_data['hostname']) == text_type

    def test_09_dashboard_os_version_ok(self):
        """
        [dashboard] 09: GET /dashboard/os_version : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/os_version' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'os_version' in dict_data \
            and type(dict_data['os_version']) == text_type

    def test_10_dashboard_databases_ok(self):
        """
        [dashboard] 10: GET /dashboard/databases : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/databases' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'databases' in dict_data \
            and 'total_size' in dict_data['databases'] \
            and type(dict_data['databases']['total_size']) == text_type \
            and 'time' in dict_data['databases'] \
            and type(dict_data['databases']['time']) == text_type \
            and 'databases' in dict_data['databases'] \
            and type(dict_data['databases']['databases']) == int \
            and dict_data['databases']['databases'] >= 0 \
            and 'total_commit' in dict_data['databases'] \
            and type(dict_data['databases']['total_commit']) == int \
            and 'total_rollback' in dict_data['databases'] \
            and type(dict_data['databases']['total_rollback']) == int

    def test_11_dashboard_pg_version_ok(self):
        """
        [dashboard] 11: GET /dashboard/pg_version : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/pg_version' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'pg_version' in dict_data \
            and type(dict_data['pg_version']) == text_type

    def test_12_dashboard_n_cpu_ok(self):
        """
        [dashboard] 12: GET /dashboard/n_cpu : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/n_cpu' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'n_cpu' in dict_data \
            and type(dict_data['n_cpu']) == int

    def test_13_dashboard_max_connections_ok(self):
        """
        [dashboard] 13: GET /dashboard/max_connections : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/max_connections' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'max_connections' in dict_data \
            and type(dict_data['max_connections']) == int

    def test_14_dashboard_config(self):
        """
        [dashboard] 14: GET /dashboard/config : HTTP return code is 200 and the data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/dashboard/config' % (
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            }
        )
        dict_data = json.loads(res)

        assert status == 200 \
            and 'history_length' in dict_data \
            and 'scheduler_interval' in dict_data
