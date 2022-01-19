import json
import re

from urllib.request import HTTPError

from .test.temboard import rand_string, temboard_request
from .conftest import ENV, pgconnect


class TestAPI:
    def test_00_env_pg(self):
        """
        [api] 00: PostgreSQL instance is up & running
        """
        with pgconnect():
            pass

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

    def test_discover(self):
        status = 0
        (status, res) = temboard_request(
            ENV["agent"]["ssl_cert_file"],
            method="GET",
            url="https://%s:%s/discover" % (
                ENV["agent"]["host"], ENV["agent"]["port"]
            ),
        )
        assert status == 200
        data = json.loads(res)
        assert set(data) == {
            "cpu",
            "hostname",
            "memory_size",
            "pg_block_size",
            "pg_data",
            "pg_port",
            "pg_version",
            "pg_version_summary",
            "plugins",
        }
        assert data["hostname"] == "test.temboard.io"
        assert data["pg_data"] == "/tmp/tests_temboard/pg/data"
        assert data["pg_block_size"] == 8192
        assert set(data["plugins"]) == {
            "monitoring",
            "dashboard",
            "pgconf",
            "administration",
            "activity",
            "maintenance",
            "statements",
        }
