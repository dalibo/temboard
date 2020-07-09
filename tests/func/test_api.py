import json
import re
import os
import sys

try:
    from urllib.request import HTTPError
except ImportError:
    from urllib2 import HTTPError

from test.temboard import rand_string, temboard_request
from conftest import ENV

# Import spc
tbda_dir = os.path.realpath(os.path.join(__file__, '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa


class TestAPI:
    def test_00_env_pg(self):
        """
        [api] 00: PostgreSQL instance is up & running
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
            assert True
        except error:
            assert False

    def test_01_login_ok(self):
        """
        [api] 01: POST /login : HTTP return code is 200 on valid credentials
        """
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
        assert status == 200

    def test_02_login_ok(self):
        """
        [api] 02: POST /login : Session ID format matches ^[a-f0-9]{64}$
        """
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
        xsession = json.loads(res)['session']
        assert re.match('^[a-f0-9]{64}$', xsession)

    def test_03_login_ko(self):
        """
        [api] 03: POST /login : Wrong password must return 404 HTTP code
        """
        status = 0
        try:
            (status, res) = temboard_request(
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/login'
                % (ENV['agent']['host'], ENV['agent']['port']),
                headers={"Content-type": "application/json"},
                data={
                    'username': ENV['agent']['user'],
                    'password': rand_string(12)
                }
            )
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
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/login'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={"Content-type": "application/json"},
                data={
                    'username': rand_string(12),
                    'password': rand_string(12)
                }
            )
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
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/login'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={"Content-type": "application/json"},
                data={
                    'username': rand_string(2),
                    'password': rand_string(12)
                }
            )
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
                ENV['agent']['ssl_cert_file'],
                method='POST',
                url='https://%s:%s/login'
                    % (ENV['agent']['host'], ENV['agent']['port']),
                headers={"Content-type": "application/json"},
                data={
                    'username': rand_string(12),
                    'password': rand_string(2)
                }
            )
        except HTTPError as e:
            status = e.code
        assert status == 406
