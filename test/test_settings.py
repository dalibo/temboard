import json
import os
import sys
import inspect
from hashlib import md5
import datetime

from test.temboard import init_env, drop_env, temboard_request

# Import spc
tbda_dir = os.path.realpath(
                os.path.abspath(
                    os.path.split(
                        inspect.getfile(
                            inspect.currentframe()))[0])+'/../temboardagent')
if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa

ENV = {}
XSESSION = ''


class TestSettings(object):

    @classmethod
    def setup_class(cls):
        global ENV
        ENV = init_env()

    @classmethod
    def teardown_class(cls):
        drop_env(ENV)

    def _exec_query(self, dbname, query):
        conn = connector(
            host=ENV['pg']['socket_dir'],
            port=ENV['pg']['port'],
            user=ENV['pg']['user'],
            password=ENV['pg']['password'],
            database=dbname
        )
        conn.connect()
        conn.execute(query)
        conn.close()
        return list(conn.get_rows())

    def _read_file(self, filepath):
        try:
            with open(filepath, 'r') as fd:
                return fd.read()
        except Exception:
            pass

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
        [settings] 00: PostgreSQL instance is up & running
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

    def test_01_get_settings_configuration_ok(self):
        """
        [settings] 01: GET /settings/configuration : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )

        # HTTP return code is 200.
        assert status == 200

        dict_data = json.loads(res)

        # Count the number of settings
        nb_settings = 0
        for cat in dict_data:
            nb_settings += len(cat['rows'])

        # dict_data length is equal to the number of category in pg_settings.
        assert len(dict_data) == self._exec_query(
                                    'postgres',
                                    "SELECT COUNT(DISTINCT(category)) AS nb "
                                    "FROM pg_settings")[0]['nb']
        # Total number of settings returned is equal to
        # the number of settings in pg_settings.
        assert nb_settings == self._exec_query(
                                'postgres',
                                "SELECT COUNT(*) AS nb "
                                "FROM pg_settings")[0]['nb']
        # Check first row's structure is right.
        assert 'context' in dict_data[0]['rows'][0]
        assert 'enumvals' in dict_data[0]['rows'][0]
        assert 'max_val' in dict_data[0]['rows'][0]
        assert 'vartype' in dict_data[0]['rows'][0]
        assert 'auto_val' in dict_data[0]['rows'][0]
        assert 'auto_val_raw' in dict_data[0]['rows'][0]
        assert 'boot_val' in dict_data[0]['rows'][0]
        assert 'unit' in dict_data[0]['rows'][0]
        assert 'desc' in dict_data[0]['rows'][0]
        assert 'name' in dict_data[0]['rows'][0]
        assert 'min_val' in dict_data[0]['rows'][0]
        assert 'setting' in dict_data[0]['rows'][0]
        assert 'setting_raw' in dict_data[0]['rows'][0]
        assert 'file_val' in dict_data[0]['rows'][0]
        assert 'file_val_raw' in dict_data[0]['rows'][0]
        assert len(dict_data[0]['rows'][0]) == 15

    def test_02_get_settings_configuration_ko_401(self):
        """
        [settings] 02: GET /settings/configuration : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_03_get_settings_configuration_ko_406(self):
        """
        [settings] 03: GET /settings/configuration : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                }
            )
        assert status == 406

    def test_04_post_settings_configuration_ok(self):
        """
        [settings] 04: POST /settings/configuration : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'settings': [
                        {'name': 'autovacuum', 'setting': 'off'}
                    ]
                }
            )

        dict_data = json.loads(res)
        q = """
SELECT
    1 AS t
FROM
    regexp_split_to_table(pg_read_file('postgresql.auto.conf'),E'\n') AS l
WHERE
    l = 'autovacuum = ''off'''
"""
        res_query = self._exec_query('postgres', q)
        # HTTP return code is 200.
        assert status == 200
        # Check new 'autovacuum' value is in postgresql.auto.conf.
        assert len(res_query) > 0
        assert res_query[0]['t'] == 1
        # Check response's structure.
        assert 'settings' in dict_data
        assert type(dict_data['settings']) == list
        assert len(dict_data['settings']) == 1
        assert type(dict_data['settings'][0]) == dict
        assert 'setting' in dict_data['settings'][0]
        assert 'restart' in dict_data['settings'][0]
        assert 'name' in dict_data['settings'][0]
        assert 'previous_setting' in dict_data['settings'][0]
        assert dict_data['settings'][0]['name'] == 'autovacuum'
        assert dict_data['settings'][0]['setting'] == 'off'

    def test_05_post_settings_configuration_ko_401(self):
        """
        [settings] 05: POST /settings/configuration : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                },
                data={
                    'settings': [
                        {'name': 'autovacuum', 'setting': 'off'}
                    ]
                }
            )
        assert status == 401

    def test_06_get_settings_configuration_ko_406(self):
        """
        [settings] 06: POST /settings/configuration : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                },
                data={
                    'settings': [
                        {'name': 'autovacuum', 'setting': 'off'}
                    ]
                }
            )
        assert status == 406

    def test_07_post_settings_configuration_ko_400(self):
        """
        [settings] 07: POST /settings/configuration : HTTP return code is 400 on invalid json data
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/configuration' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data=''
            )
        assert status == 400

    def test_08_get_settings_configuration_status_ok(self):
        """
        [settings] 08: GET /settings/configuration/status : HTTP return code is 200 and the response data structure is right
        """  # noqa
        # shared_buffers update requires the server to restart
        self._exec_query(
                'postgres',
                "ALTER SYSTEM SET shared_buffers TO '256MB'"
            )
        # autovacuum update requires the server to reload
        self._exec_query(
                'postgres',
                "ALTER SYSTEM SET autovacuum TO 'on'"
            )
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/status' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data=''
            )
        dict_data = json.loads(res)
        # HTTP return code is 200.
        assert status == 200
        assert 'restart_pending' in dict_data
        assert 'restart_changes' in dict_data
        assert 'reload_pending' in dict_data
        assert 'reload_changes' in dict_data
        assert type(dict_data['restart_changes']) == list
        assert type(dict_data['reload_changes']) == list
        assert dict_data['restart_pending'] is True
        assert dict_data['reload_pending'] is True
        assert type(dict_data['restart_changes']) == list
        assert type(dict_data['reload_changes']) == list
        assert len(dict_data['restart_changes']) == 1
        assert len(dict_data['reload_changes']) == 1
        assert type(dict_data['restart_changes'][0]) == dict
        assert type(dict_data['reload_changes'][0]) == dict
        assert 'context' in dict_data['restart_changes'][0]
        assert 'enumvals' in dict_data['restart_changes'][0]
        assert 'max_val' in dict_data['restart_changes'][0]
        assert 'vartype' in dict_data['restart_changes'][0]
        assert 'auto_val' in dict_data['restart_changes'][0]
        assert 'auto_val_raw' in dict_data['restart_changes'][0]
        assert 'boot_val' in dict_data['restart_changes'][0]
        assert 'setting' in dict_data['restart_changes'][0]
        assert 'setting_raw' in dict_data['restart_changes'][0]
        assert 'file_val' in dict_data['restart_changes'][0]
        assert 'file_val_raw' in dict_data['restart_changes'][0]
        assert 'min_val' in dict_data['restart_changes'][0]
        assert 'pending_val' in dict_data['restart_changes'][0]
        assert 'unit' in dict_data['restart_changes'][0]
        assert 'desc' in dict_data['restart_changes'][0]
        assert 'name' in dict_data['restart_changes'][0]
        assert len(dict_data['restart_changes'][0]) == 16
        assert 'context' in dict_data['reload_changes'][0]
        assert 'enumvals' in dict_data['reload_changes'][0]
        assert 'max_val' in dict_data['reload_changes'][0]
        assert 'vartype' in dict_data['reload_changes'][0]
        assert 'setting' in dict_data['restart_changes'][0]
        assert 'setting_raw' in dict_data['restart_changes'][0]
        assert 'auto_val' in dict_data['reload_changes'][0]
        assert 'auto_val_raw' in dict_data['reload_changes'][0]
        assert 'boot_val' in dict_data['reload_changes'][0]
        assert 'file_val' in dict_data['reload_changes'][0]
        assert 'file_val_raw' in dict_data['reload_changes'][0]
        assert 'min_val' in dict_data['reload_changes'][0]
        assert 'pending_val' in dict_data['reload_changes'][0]
        assert 'unit' in dict_data['reload_changes'][0]
        assert 'desc' in dict_data['reload_changes'][0]
        assert 'name' in dict_data['reload_changes'][0]
        assert len(dict_data['reload_changes'][0]) == 16

    def test_09_get_settings_configuration_status_ko_406(self):
        """
        [settings] 09: GET /settings/configuration/status : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/status' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                }
            )
        assert status == 406

    def test_10_get_settings_configuration_status_ko_401(self):
        """
        [settings] 10: GET /settings/configuration/status : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/status' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_11_get_settings_configuration_categories(self):
        """
        [settings] 11: GET /settings/configuration/categories : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/categories' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)

        assert status == 200
        assert 'categories' in dict_data
        assert type(dict_data['categories']) == list
        assert len(dict_data['categories']) == \
            self._exec_query(
                'postgres',
                "SELECT COUNT(DISTINCT(category)) AS nb "
                "FROM pg_settings")[0]['nb']
        assert dict_data['categories'][0] == \
            self._exec_query(
                'postgres',
                "SELECT category FROM pg_settings "
                "ORDER BY category LIMIT 1")[0]['category']

    def test_12_get_settings_configuration_categories_ko_401(self):
        """
        [settings] 12: GET /settings/configuration/categories : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/categories' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_13_get_settings_configuration_categories_ko_406(self):
        """
        [settings] 13: GET /settings/configuration/categories : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/categories' % (
                    ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                }
            )
        assert status == 406

    def test_14_get_settings_configuration_category_ok(self):
        """
        [settings] 14: GET /settings/configuration/category/:categoryname : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/category/Autovacuum'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)

        # Count the number of settings
        nb_settings = 0
        for cat in dict_data:
            nb_settings += len(cat['rows'])

        assert status == 200
        assert len(dict_data) == 1
        assert nb_settings == self._exec_query(
                                'postgres',
                                "SELECT COUNT(*) AS nb FROM pg_settings "
                                "WHERE category = 'Autovacuum'")[0]['nb']
        assert 'context' in dict_data[0]['rows'][0]
        assert 'enumvals' in dict_data[0]['rows'][0]
        assert 'max_val' in dict_data[0]['rows'][0]
        assert 'vartype' in dict_data[0]['rows'][0]
        assert 'auto_val' in dict_data[0]['rows'][0]
        assert 'auto_val_raw' in dict_data[0]['rows'][0]
        assert 'boot_val' in dict_data[0]['rows'][0]
        assert 'unit' in dict_data[0]['rows'][0]
        assert 'desc' in dict_data[0]['rows'][0]
        assert 'name' in dict_data[0]['rows'][0]
        assert 'min_val' in dict_data[0]['rows'][0]
        assert 'setting' in dict_data[0]['rows'][0]
        assert 'setting_raw' in dict_data[0]['rows'][0]
        assert 'file_val' in dict_data[0]['rows'][0]
        assert 'file_val_raw' in dict_data[0]['rows'][0]
        assert len(dict_data[0]['rows'][0]) == 15

    def test_15_get_settings_configuration_category_ko_401(self):
        """
        [settings] 15: GET /settings/configuration/category/:categoryname : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/category/Autovacuum'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_16_get_settings_configuration_category_ko_406(self):
        """
        [settings] 16: GET /settings/configuration/category/:categoryname : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/configuration/category/Autovacuum'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                }
            )
        assert status == 406

    def test_17_get_settings_hba_ok(self):
        """
        [settings] 17: GET /settings/hba : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'version' in dict_data
        assert 'filepath' in dict_data
        assert dict_data['version'] is None
        assert type(dict_data['filepath']) == unicode
        assert 'entries' in dict_data
        assert len(dict_data['entries']) > 0
        for row in dict_data['entries']:
            if 'comment' not in row:
                assert 'connection' in row
                assert 'database' in row
                assert 'user' in row
                assert 'address' in row
                assert 'auth_method' in row
                assert 'auth_options' in row
            else:
                assert 'comment' in row

    def test_18_get_settings_hba_ko_401(self):
        """
        [settings] 18: GET /settings/hba : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_19_get_settings_hba_ko_406(self):
        """
        [settings] 19: GET /settings/hba : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                }
            )
        assert status == 406

    def test_20_get_settings_hba_raw_ok(self):
        """
        [settings] 20: GET /settings/hba/raw : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        md5sum_hba = self._exec_query(
                        'postgres',
                        "SELECT md5(pg_read_file('pg_hba.conf')) "
                        "AS md5sum_hba")[0]['md5sum_hba']
        assert status == 200
        assert 'version' in dict_data
        assert 'filepath' in dict_data
        assert dict_data['version'] is None
        assert type(dict_data['filepath']) == unicode
        assert 'content' in dict_data
        assert md5(dict_data['content']).hexdigest() == md5sum_hba

    def test_21_get_settings_hba_raw_ko_401(self):
        """
        [settings] 21: GET /settings/hba/raw : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_22_get_settings_hba_raw_ko_406(self):
        """
        [settings] 22: GET /settings/hba/raw : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "X" * 12
                }
            )
        assert status == 406

    def test_23_post_settings_hba_ok(self):
        """
        [settings] 23: POST /settings/hba : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'entries':
                    [
                        {
                            'connection': 'local',
                            'database': 'all',
                            'user': 'all',
                            'auth_method': 'trust',
                            'auth_options': 'blahblah'
                        },
                        {
                            'connection': 'host',
                            'database': 'test',
                            'user': 'test',
                            'address': '192.168.1.0/24',
                            'auth_method': 'trust'
                        },
                        {
                            'connection': 'hostssl',
                            'database': 'test2',
                            'user': 'test2',
                            'address': '192.168.1.0 255.255.255.0',
                            'auth_method': 'trust'
                        }
                    ]
                }
            )
        dict_data = json.loads(res)
        md5sum_hba = self._exec_query(
                        'postgres',
                        "SELECT md5(pg_read_file('pg_hba.conf')) "
                        "AS md5sum_hba")[0]['md5sum_hba']
        # Expected hba raw content.
        exp_hba_raw = "local  all  all  trust blahblah\r\nhost  test  test 192.168.1.0/24 trust \r\nhostssl  test2  test2 192.168.1.0 255.255.255.0 trust \r\n"  # noqa
        assert status == 200
        assert type(dict_data) == dict
        assert 'last_version' in dict_data
        assert 'filepath' in dict_data
        assert md5sum_hba == md5(exp_hba_raw).hexdigest()

    def test_24_post_settings_hba_ko_401(self):
        """
        [settings] 24: POST /settings/hba : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                },
                data={
                    'entries':
                    [
                        {
                            'connection': 'local',
                            'database': 'all',
                            'user': 'all',
                            'auth_method': 'trust',
                            'auth_options': 'blahblah'
                        }
                    ]
                }
            )
        assert status == 401

    def test_25_post_settings_hba_ko_406(self):
        """
        [settings] 25: POST /settings/hba : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                },
                data={
                    'entries':
                    [
                        {
                            'connection': 'local',
                            'database': 'all',
                            'user': 'all',
                            'auth_method': 'trust',
                            'auth_options': 'blahblah'
                        }
                    ]
                }
            )
        assert status == 406

    def test_26_post_settings_hba_ko_406(self):
        """
        [settings] 26: POST /settings/hba : HTTP return code is 406 on invalid data
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                },
                data={'toto': 'tutu'}
            )
        assert status == 406

    def test_27_post_settings_hba_version_ok(self):
        """
        [settings] 27: POST /settings/hba : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'entries':
                    [
                        {
                            'connection': 'local',
                            'database': 'all',
                            'user': 'all',
                            'auth_method': 'trust'
                        }
                    ],
                    'new_version': True
                }
            )
        dict_data = json.loads(res)
        md5sum_hba = self._exec_query(
                        'postgres',
                        "SELECT md5(pg_read_file('pg_hba.conf')) "
                        "AS md5sum_hba")[0]['md5sum_hba']
        # Expected hba raw content.
        exp_hba_raw = "local  all  all  trust \r\n"

        assert status == 200
        assert type(dict_data) == dict
        assert 'last_version' in dict_data
        try:
            datetime.datetime.strptime(
                            dict_data['last_version'],
                            "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            assert False
        assert 'filepath' in dict_data
        assert md5sum_hba == md5(exp_hba_raw).hexdigest()

    def test_28_get_settings_hba_versions_ok(self):
        """
        [settings] 28: GET /settings/hba/versions: HTTP return code is 200 and the repsonse date structure is right.
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/versions' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'filepath' in dict_data
        assert 'versions' in dict_data
        assert type(dict_data['versions']) == list
        assert len(dict_data['versions']) == 1
        assert os.path.isfile("%s.%s" % (
                dict_data['filepath'],
                dict_data['versions'][0]))

    def test_29_get_settings_hba_versions_ko_401(self):
        """
        [settings] 29: GET /settings/hba/versions: HTTP return code is 401 on invalid xsession.
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/versions' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_30_get_settings_hba_versions_ko_406(self):
        """
        [settings] 30: GET /settings/hba/versions: HTTP return code is 406 on malformed xsession.
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/versions' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "XXXXXXXXXXX"
                }
            )
        assert status == 406

    def test_31_get_settings_hba_version_ok(self):
        """
        [settings] 31: GET /settings/hba?version=:version : HTTP return code is 200 and the response data structure is right
        """  # noqa
        # We need to get the last version id.
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/versions' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'filepath' in dict_data
        assert 'versions' in dict_data
        assert type(dict_data['versions']) == list
        assert len(dict_data['versions']) == 1
        assert os.path.isfile("%s.%s" % (
            dict_data['filepath'],
            dict_data['versions'][0]
            )
        )
        last_version = dict_data['versions'][0]
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        last_version
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'version' in dict_data
        assert 'filepath' in dict_data
        assert dict_data['version'] == last_version
        assert type(dict_data['filepath']) == unicode
        assert 'entries' in dict_data
        assert len(dict_data['entries']) > 0
        assert 'connection' in dict_data['entries'][0]
        assert 'database' in dict_data['entries'][0]
        assert 'user' in dict_data['entries'][0]
        assert 'address' in dict_data['entries'][0]
        assert 'auth_method' in dict_data['entries'][0]
        assert 'auth_options' in dict_data['entries'][0]

    def test_32_get_settings_hba_version_ko_404(self):
        """
        [settings] 32: GET /settings/hba?version=:version : HTTP return code is 404 on unexisting version
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba?version=1970-01-01T00:00:01' %
                    (ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        assert status == 404

    def test_33_get_settings_hba_version_ko_406(self):
        """
        [settings] 33: GET /settings/hba?version=:version : HTTP return code is 406 on malformed version id
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba?version=XX112233' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        assert status == 406

    def test_34_get_settings_hba_raw_version_ok(self):
        """
        [settings] 34: GET /settings/hba/raw?version=:version : HTTP return code is 200 and the response data structure is right
        """  # noqa
        # We need to get the last version id.
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/versions' % (
                        ENV['agent']['host'], ENV['agent']['port']),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'filepath' in dict_data
        assert 'versions' in dict_data
        assert type(dict_data['versions']) == list
        assert len(dict_data['versions']) == 1
        assert os.path.isfile("%s.%s" % (
                dict_data['filepath'],
                dict_data['versions'][0]
                )
            )
        last_version = dict_data['versions'][0]
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/raw?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        last_version
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'version' in dict_data
        assert 'filepath' in dict_data
        assert dict_data['version'] == last_version
        assert type(dict_data['filepath']) == unicode
        assert 'content' in dict_data
        assert md5(dict_data['content']).hexdigest() == \
            md5(self._read_file("%s.%s" % (
                dict_data['filepath'],
                last_version)
                )).hexdigest()

    def test_35_get_settings_hba_raw_version_ko_404(self):
        """
        [settings] 35: GET /settings/hba/raw?version=:version : HTTP return code is 404 on unexisting version
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/raw?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        '1970-01-01T00:00:01'
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        assert status == 404

    def test_36_get_settings_hba_raw_version_ko_406(self):
        """
        [settings] 36: GET /settings/hba/raw?version=:version : HTTP return code is 406 on malformed version id
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/raw?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        'XX112233'
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        assert status == 406

    def test_37_delete_settings_hba_version_ok(self):
        """
        [settings] 37: DELETE /settings/hba/raw?version=:version : HTTP return code is 200 and data structure is right
        """  # noqa
        # We need to get the last version id.
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/hba/versions' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'filepath' in dict_data
        assert 'versions' in dict_data
        assert type(dict_data['versions']) == list
        assert len(dict_data['versions']) == 1
        assert os.path.isfile("%s.%s" % (
                dict_data['filepath'],
                dict_data['versions'][0]
                )
            )
        last_version = dict_data['versions'][0]
        filepath = dict_data['filepath']
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='DELETE',
                url='https://%s:%s/settings/hba?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        last_version
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        assert status == 200
        assert 'deleted' in dict_data
        assert 'version' in dict_data
        assert dict_data['version'] == last_version
        assert dict_data['deleted'] is True
        assert not os.path.isfile("%s.%s" % (filepath, last_version))

    def test_38_delete_settings_hba_version_ko_401(self):
        """
        [settings] 38: DELETE /settings/hba/raw?version=:version : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='DELETE',
                url='https://%s:%s/settings/hba?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        '1970-01-01T00:00:01'
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_39_delete_settings_hba_version_ko_406(self):
        """
        [settings] 39: DELETE /settings/hba/raw?version=:version : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='DELETE',
                url='https://%s:%s/settings/hba?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        '1970-01-01T00:00:01'
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 12
                }
            )
        assert status == 406

    def test_40_delete_settings_hba_version_ko_406(self):
        """
        [settings] 40: DELETE /settings/hba/raw?version=:version : HTTP return code is 406 on malformed version id
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='DELETE',
                url='https://%s:%s/settings/hba?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        'A' * 6
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        assert status == 406

    def test_41_delete_settings_hba_version_ko_404(self):
        """
        [settings] 41: DELETE /settings/hba/raw?version=:version : HTTP return code is 404 on unexisting version
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='DELETE',
                url='https://%s:%s/settings/hba?version=%s' % (
                        ENV['agent']['host'],
                        ENV['agent']['port'],
                        '1970-01-01T00:00:01'
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        assert status == 404

    def test_42_get_settings_pg_ident_ok(self):
        """
        [settings] 42: GET /settings/pg_ident : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        dict_data = json.loads(res)
        md5sum_pg_ident = self._exec_query(
                            'postgres',
                            "SELECT md5(pg_read_file('pg_ident.conf')) "
                            "AS md5sum_pg_ident")[0]['md5sum_pg_ident']
        assert status == 200
        assert 'filepath' in dict_data
        assert type(dict_data['filepath']) == unicode
        assert 'content' in dict_data
        assert md5(dict_data['content']).hexdigest() == md5sum_pg_ident

    def test_43_get_settings_pg_ident_ko_401(self):
        """
        [settings] 43: GET /settings/pg_ident : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                }
            )
        assert status == 401

    def test_44_get_settings_pg_ident_ko_406(self):
        """
        [settings] 44: GET /settings/pg_ident : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "X" * 12
                }
            )
        assert status == 406

    def test_45_post_settings_hba_raw_ok(self):
        """
        [settings] 45: POST /settings/hba/raw : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'content': 'local all all trust',
                    'new_version': True
                }
            )
        dict_data = json.loads(res)
        md5sum_hba = self._exec_query(
                        'postgres',
                        "SELECT md5(pg_read_file('pg_hba.conf')) "
                        "AS md5sum_hba")[0]['md5sum_hba']
        # Expected hba raw content.
        exp_hba_raw = "local all all trust"

        assert status == 200
        assert type(dict_data) == dict
        assert 'last_version' in dict_data
        try:
            datetime.datetime.strptime(
                            dict_data['last_version'],
                            "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            assert False
        assert 'filepath' in dict_data
        assert md5sum_hba == md5(exp_hba_raw).hexdigest()

    def test_46_post_settings_hba_raw_ko_401(self):
        """
        [settings] 46: POST /settings/hba/raw : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                },
                data={
                    'content': 'local all all trust',
                    'new_version': True
                }
            )
        assert status == 401

    def test_47_post_settings_hba_raw_ko_406(self):
        """
        [settings] 47: POST /settings/hba/raw : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "X" * 12
                },
                data={
                    'content': 'local all all trust',
                    'new_version': True
                }
            )
        assert status == 406

    def test_48_post_settings_hba_raw_ko_406(self):
        """
        [settings] 48: POST /settings/hba/raw : HTTP return code is 406 on invalid data
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/hba/raw' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'toto': 'tutu'
                }
            )
        assert status == 406

    def test_49_post_settings_pg_ident_ok(self):
        """
        [settings] 49: POST /settings/pg_ident : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'content': '# test\r\n# test\r\n'
                }
            )
        dict_data = json.loads(res)
        md5sum_pg_ident = self._exec_query(
                            'postgres',
                            "SELECT md5(pg_read_file('pg_ident.conf')) AS "
                            "md5sum_pg_ident")[0]['md5sum_pg_ident']
        # Expected hba raw content.
        exp_pg_ident_raw = "# test\r\n# test\r\n"

        assert status == 200
        assert type(dict_data) == dict
        assert 'update' in dict_data
        assert dict_data['update'] is True
        assert md5sum_pg_ident == md5(exp_pg_ident_raw).hexdigest()

    def test_50_post_settings_pg_ident_ko_401(self):
        """
        [settings] 50: POST /settings/pg_ident : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "3" * 64
                },
                data={
                    'content': '# test\r\n# test\r\n'
                }
            )
        assert status == 401

    def test_51_post_settings_pg_ident_ko_406(self):
        """
        [settings] 51: POST /settings/pg_ident : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": "X" * 12
                },
                data={
                    'content': '# test\r\n# test\r\n'
                }
            )
        assert status == 406

    def test_52_post_settings_pg_ident_ko_406(self):
        """
        [settings] 52: POST /settings/pg_ident : HTTP return code is 406 on invalid data
        """  # noqa
        (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/settings/pg_ident' % (
                        ENV['agent']['host'],
                        ENV['agent']['port']
                    ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                },
                data={
                    'toto': 'tutu'
                }
            )
        assert status == 406
