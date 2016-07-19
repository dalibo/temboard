import json
import re
import time

from urllib2 import HTTPError
from test.temboard import init_env, drop_env, rand_string, temboard_request
import test.configuration as cf
from test.spc import connector, error

ENV = {}

class TestAPI:

    @classmethod
    def setup_class(cls):
        global ENV
        ENV = init_env()

    @classmethod
    def teardown_class(cls):
        drop_env(ENV)

    def test_00_env_pg(self):
        """
        [api] 00: PostgreSQL instance is up & running
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
            assert True
        except error as e:
            assert False

    def test_01_login_ok(self):
        """
        [api] 01: POST /login : HTTP return code is 200 on valid credentials
        """
        (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': cf.G_USER, 'password': cf.G_PASSWORD})
        assert status == 200

    def test_02_login_ok(self):
        """
        [api] 02: POST /login : Session ID format matches ^[a-f0-9]{64}$
        """
        (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': cf.G_USER, 'password': cf.G_PASSWORD})
        xsession = json.loads(res)['session']
        assert re.match('^[a-f0-9]{64}$', xsession)

    def test_03_login_ko(self):
        """
        [api] 03: POST /login : Wrong password must return 404 HTTP code
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': cf.G_USER, 'password': rand_string(12)})
        except HTTPError as e:
            status = e.code
        assert status == 404

    def test_04_login_ko(self):
        """
        [api] 04: POST /login : Wrong username must return 404 HTTP code
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': rand_string(12), 'password': rand_string(12)})
        except HTTPError as e:
            status = e.code
        assert status == 404

    def test_05_login_ko(self):
        """
        [api] 05: POST /login : Bad username format must return 406 HTTP code
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': rand_string(2), 'password': rand_string(12)})
        except HTTPError as e:
            status = e.code
        assert status == 406

    def test_06_login_ko(self):
        """
        [api] 06: POST /login : Bad password format must return 406 HTTP code
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['g_ssl_cert_file_path'],
                method = 'POST',
                url = 'https://%s:%s/login' % (cf.G_HOST, cf.G_PORT),
                headers = {"Content-type": "application/json"},
                data = {'username': rand_string(12), 'password': rand_string(2)})
        except HTTPError as e:
            status = e.code
        assert status == 406
