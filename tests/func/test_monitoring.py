from __future__ import absolute_import

import json
import os
import sys

try:
    from urllib.request import HTTPError
except ImportError:
    from urllib2 import HTTPError

from .test.temboard import temboard_request
from .conftest import ENV

# Import spc
tbda_dir = os.path.realpath(os.path.join(__file__, '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa

XSESSION = ''


class TestMonitoring:
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

    def test_01_monitoring_session(self):
        """
        [monitoring] 01: GET /monitoring/probe/sessions : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/sessions' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_02_monitoring_xacts(self):
        """
        [monitoring] 02: GET /monitoring/probe/xacts : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/xacts' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_03_monitoring_locks(self):
        """
        [monitoring] 03: GET /monitoring/probe/locks : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/locks' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_04_monitoring_blocks(self):
        """
        [monitoring] 04: GET /monitoring/probe/blocks : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/blocks' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_05_monitoring_bgwriter(self):
        """
        [monitoring] 05: GET /monitoring/probe/bgwriter : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/bgwriter' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_06_monitoring_db_size(self):
        """
        [monitoring] 06: GET /monitoring/probe/db_size : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/db_size' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_07_monitoring_tblspc_size(self):
        """
        [monitoring] 07: GET /monitoring/probe/tblspc_size : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/tblspc_size' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_08_monitoring_filesystems_size(self):
        """
        [monitoring] 08: GET /monitoring/probe/filesystems_size : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/filesystems_size' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_09_monitoring_cpu(self):
        """
        [monitoring] 09: GET /monitoring/probe/cpu : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/cpu' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_10_monitoring_process(self):
        """
        [monitoring] 10: GET /monitoring/probe/process : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/process' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_11_monitoring_memory(self):
        """
        [monitoring] 11: GET /monitoring/probe/memory : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/memory' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_12_monitoring_loadavg(self):
        """
        [monitoring] 12: GET /monitoring/probe/loadavg : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/loadavg' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_13_monitoring_wal_files(self):
        """
        [monitoring] 13: GET /monitoring/probe/wal_files : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/wal_files' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_14_monitoring_replication_lag(self):
        """
        [monitoring] 14: GET /monitoring/probe/replication_lag : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/replication_lag' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_15_monitoring_temp_files_size_delta(self):
        """
        [monitoring] 15: GET /monitoring/probe/temp_files_size_delta : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/temp_files_size_delta' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_16_monitoring_replication_connection(self):
        """
        [monitoring] 16: GET /monitoring/probe/replication_connection : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/replication_connection' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_17_monitoring_heap_bloat(self):
        """
        [monitoring] 17: GET /monitoring/probe/heap_bloat : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/heap_bloat' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200

    def test_18_monitoring_btree_bloat(self):
        """
        [monitoring] 18: GET /monitoring/probe/btree_bloat : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/monitoring/probe/btree_bloat' % (
                    ENV['agent']['host'],
                    ENV['agent']['port']
                ),
                headers={
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200
