import json
import re
import time

from urllib2 import HTTPError
from test.temboard import init_env, drop_env, rand_string, temboard_request
import test.configuration as cf
from test.spc import connector, error

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
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': cf.G_USER, 'password': cf.G_PASSWORD})
        return json.loads(res)['session']

    def test_00_env_pg(self):
        """
        [supervision] 00: PostgreSQL instance is up & running
        """
        conn = connector(
            host = ENV['pg_sockdir'],
            port = cf.PG_PORT,
            user = cf.PG_USER,
            password = cf.PG_PASSWORD,
            database = 'postgres'
        )
        try:
            conn.connect()
            conn.close()
            global XSESSION
            XSESSION = self._temboard_login()
            assert True
        except error as e:
            assert False

    def test_01_supervision_session(self):
        """
        [supervision] 01: GET /supervision/probe/sessions : Check HTTP code returned is 200
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/sessions' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/xacts' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/locks' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/blocks' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/bgwriter' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/db_size' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/tblspc_size' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/filesystems_size' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/cpu' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/process' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/memory' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/loadavg' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/wal_files' % (cf.G_HOST, cf.G_PORT),
                headers = {
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
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'GET',
                url = 'https://%s:%s/supervision/probe/replication' % (cf.G_HOST, cf.G_PORT),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": XSESSION
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 200
