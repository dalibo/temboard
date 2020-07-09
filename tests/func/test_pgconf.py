from __future__ import absolute_import

import json
import os
import sys
from hashlib import md5
import datetime
import pytest

from .test.temboard import temboard_request
from .conftest import ENV

# Import spc
tbda_dir = os.path.realpath(os.path.join(__file__, '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa

XSESSION = ''


class TestPgconf(object):
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
                ENV['agent']['host'],
                ENV['agent']['port']
            ),
            headers={"Content-type": "application/json"},
            data={
                'username': ENV['agent']['user'],
                'password': ENV['agent']['password']
            }
        )
        return json.loads(res)['session']

    def test_00_env_pg(self):
        """
        [pgconf] 00: PostgreSQL instance is up & running
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

    def test_01_get_pgconf_configuration_ok(self):
        """
        [pgconf] 01: GET /pgconf/configuration : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration' % (
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
        r = self._exec_query('postgres',
                             "SELECT COUNT(DISTINCT(category)) AS nb "
                             "FROM pg_settings")
        assert len(dict_data) == r[0]['nb']
        # Total number of settings returned is equal to
        # the number of settings in pg_settings.
        r = self._exec_query('postgres',
                             "SELECT COUNT(*) AS nb FROM pg_settings")
        assert nb_settings == r[0]['nb']
        # Check first row's structure is right.
        assert 'context' in dict_data[0]['rows'][0]
        assert 'enumvals' in dict_data[0]['rows'][0]
        assert 'max_val' in dict_data[0]['rows'][0]
        assert 'vartype' in dict_data[0]['rows'][0]
        assert 'boot_val' in dict_data[0]['rows'][0]
        assert 'reset_val' in dict_data[0]['rows'][0]
        assert 'unit' in dict_data[0]['rows'][0]
        assert 'desc' in dict_data[0]['rows'][0]
        assert 'name' in dict_data[0]['rows'][0]
        assert 'min_val' in dict_data[0]['rows'][0]
        assert 'setting' in dict_data[0]['rows'][0]
        assert 'setting_raw' in dict_data[0]['rows'][0]
        assert 'pending_restart' in dict_data[0]['rows'][0]
        assert len(dict_data[0]['rows'][0]) == 13

    def test_02_get_pgconf_configuration_ko_401(self):
        """
        [pgconf] 02: GET /pgconf/configuration : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "3" * 64
            }
        )
        assert status == 401

    def test_03_get_pgconf_configuration_ko_406(self):
        """
        [pgconf] 03: GET /pgconf/configuration : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "XXXXXXXXXXX"
            }
        )
        assert status == 406

    def test_04_post_pgconf_configuration_ok(self):
        """
        [pgconf] 04: POST /pgconf/configuration : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (
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

    def test_05_post_pgconf_configuration_ko_401(self):
        """
        [pgconf] 05: POST /pgconf/configuration : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (
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

    def test_06_get_pgconf_configuration_ko_406(self):
        """
        [pgconf] 06: POST /pgconf/configuration : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (
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

    def test_07_post_pgconf_configuration_ko_400(self):
        """
        [pgconf] 07: POST /pgconf/configuration : HTTP return code is 400 on invalid json data
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            },
            data=''
        )
        assert status == 400

    def test_08_get_pgconf_configuration_status_ok(self):
        """
        [pgconf] 08: GET /pgconf/configuration/status : HTTP return code is 200 and the response data structure is right
        """  # noqa
        # shared_buffers update requires the server to restart
        self._exec_query('postgres',
                         "ALTER SYSTEM SET shared_buffers TO '256MB'")
        self._exec_query('postgres', "SELECT pg_reload_conf()")
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/status' % (
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
        assert type(dict_data['restart_changes']) == list
        assert dict_data['restart_pending'] is True
        assert type(dict_data['restart_changes']) == list
        assert len(dict_data['restart_changes']) == 1
        assert type(dict_data['restart_changes'][0]) == dict
        assert 'context' in dict_data['restart_changes'][0]
        assert 'enumvals' in dict_data['restart_changes'][0]
        assert 'max_val' in dict_data['restart_changes'][0]
        assert 'vartype' in dict_data['restart_changes'][0]
        assert 'boot_val' in dict_data['restart_changes'][0]
        assert 'reset_val' in dict_data['restart_changes'][0]
        assert 'setting' in dict_data['restart_changes'][0]
        assert 'setting_raw' in dict_data['restart_changes'][0]
        assert 'min_val' in dict_data['restart_changes'][0]
        assert 'unit' in dict_data['restart_changes'][0]
        assert 'desc' in dict_data['restart_changes'][0]
        assert 'name' in dict_data['restart_changes'][0]
        assert 'pending_restart' in dict_data['restart_changes'][0]
        assert len(dict_data['restart_changes'][0]) == 13

    def test_09_get_pgconf_configuration_status_ko_406(self):
        """
        [pgconf] 09: GET /pgconf/configuration/status : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/status' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "XXXXXXXXXXX"
            }
        )
        assert status == 406

    def test_10_get_pgconf_configuration_status_ko_401(self):
        """
        [pgconf] 10: GET /pgconf/configuration/status : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/status' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "3" * 64
            }
        )
        assert status == 401

    def test_11_get_pgconf_configuration_categories(self):
        """
        [pgconf] 11: GET /pgconf/configuration/categories : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/categories' % (
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

    def test_12_get_pgconf_configuration_categories_ko_401(self):
        """
        [pgconf] 12: GET /pgconf/configuration/categories : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/categories' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "3" * 64
            }
        )
        assert status == 401

    def test_13_get_pgconf_configuration_categories_ko_406(self):
        """
        [pgconf] 13: GET /pgconf/configuration/categories : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/categories' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "XXXXXXXXXXX"
            }
        )
        assert status == 406

    def test_14_get_pgconf_configuration_category_ok(self):
        """
        [pgconf] 14: GET /pgconf/configuration/category/:categoryname : HTTP return code is 200 and the response data structure is right
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/category/Autovacuum'
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

        r = self._exec_query('postgres',
                             "SELECT COUNT(*) AS nb FROM pg_settings "
                             "WHERE category = 'Autovacuum'")
        assert status == 200
        assert len(dict_data) == 1
        assert nb_settings == r[0]['nb']
        assert 'context' in dict_data[0]['rows'][0]
        assert 'enumvals' in dict_data[0]['rows'][0]
        assert 'max_val' in dict_data[0]['rows'][0]
        assert 'vartype' in dict_data[0]['rows'][0]
        assert 'boot_val' in dict_data[0]['rows'][0]
        assert 'reset_val' in dict_data[0]['rows'][0]
        assert 'unit' in dict_data[0]['rows'][0]
        assert 'desc' in dict_data[0]['rows'][0]
        assert 'name' in dict_data[0]['rows'][0]
        assert 'min_val' in dict_data[0]['rows'][0]
        assert 'setting' in dict_data[0]['rows'][0]
        assert 'setting_raw' in dict_data[0]['rows'][0]
        assert 'pending_restart' in dict_data[0]['rows'][0]
        assert len(dict_data[0]['rows'][0]) == 13

    def test_15_get_pgconf_configuration_category_ko_401(self):
        """
        [pgconf] 15: GET /pgconf/configuration/category/:categoryname : HTTP return code is 401 on invalid xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/category/Autovacuum'
                % (ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "3" * 64
            }
        )
        assert status == 401

    def test_16_get_pgconf_configuration_category_ko_406(self):
        """
        [pgconf] 16: GET /pgconf/configuration/category/:categoryname : HTTP return code is 406 on malformed xsession
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='GET',
            url='https://%s:%s/pgconf/configuration/category/Autovacuum'
                % (ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": "XXXXXXXXXXX"
            }
        )
        assert status == 406

    @pytest.mark.skipif("ENV['pg']['version'] < 12")
    def test_17_post_pgconf_configuration_ok_int_or_real(self):
        """
        [pgconf] 17: POST /pgconf/configuration : HTTP return code is 200 for
        settings that are either integer or real depending on version
        autovacuum_vacuum_cost_delay is of type real for PG12 but integer
        before
        """  # noqa
        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            },
            data={
                'settings': [
                    {'name': 'autovacuum_vacuum_cost_delay',
                     'setting': '2ms'}
                ]
            }
        )
        assert status == 200

        (status, res) = temboard_request(
            ENV['agent']['ssl_cert_file'],
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (
                ENV['agent']['host'], ENV['agent']['port']),
            headers={
                "Content-type": "application/json",
                "X-Session": XSESSION
            },
            data={
                'settings': [
                    {'name': 'autovacuum_vacuum_cost_delay',
                     'setting': '0.2ms'}
                ]
            }
        )
        assert status == 200

        r = self._exec_query('postgres',
                             "SELECT setting FROM pg_settings "
                             "WHERE name = 'autovacuum_vacuum_cost_delay'")
        assert 0.2 == float(r[0]['setting'])
