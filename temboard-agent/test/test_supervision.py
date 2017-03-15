import json
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


class TestSupervision:

    @classmethod
    def setup_class(cls):
        global ENV
        ENV = init_env()

    @classmethod
    def teardown_class(cls):
        drop_env(ENV)

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

    def test_01_supervision_session(self):
        """
        [supervision] 01: GET /supervision/probe/sessions : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/sessions' % (
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

    def test_02_supervision_xacts(self):
        """
        [supervision] 02: GET /supervision/probe/xacts : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/xacts' % (
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

    def test_03_supervision_locks(self):
        """
        [supervision] 03: GET /supervision/probe/locks : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/locks' % (
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

    def test_04_supervision_blocks(self):
        """
        [supervision] 04: GET /supervision/probe/blocks : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/blocks' % (
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

    def test_05_supervision_bgwriter(self):
        """
        [supervision] 05: GET /supervision/probe/bgwriter : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/bgwriter' % (
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

    def test_06_supervision_db_size(self):
        """
        [supervision] 06: GET /supervision/probe/db_size : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/db_size' % (
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

    def test_07_supervision_tblspc_size(self):
        """
        [supervision] 07: GET /supervision/probe/tblspc_size : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/tblspc_size' % (
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

    def test_08_supervision_filesystems_size(self):
        """
        [supervision] 08: GET /supervision/probe/filesystems_size : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/filesystems_size' % (
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

    def test_09_supervision_cpu(self):
        """
        [supervision] 09: GET /supervision/probe/cpu : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/cpu' % (
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

    def test_10_supervision_process(self):
        """
        [supervision] 10: GET /supervision/probe/process : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/process' % (
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

    def test_11_supervision_memory(self):
        """
        [supervision] 11: GET /supervision/probe/memory : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/memory' % (
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

    def test_12_supervision_loadavg(self):
        """
        [supervision] 12: GET /supervision/probe/loadavg : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/loadavg' % (
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

    def test_13_supervision_wal_files(self):
        """
        [supervision] 13: GET /supervision/probe/wal_files : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/wal_files' % (
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

    def test_14_supervision_replication(self):
        """
        [supervision] 14: GET /supervision/probe/replication : Check HTTP code returned is 200
        """  # noqa
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='GET',
                url='https://%s:%s/supervision/probe/replication' % (
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
