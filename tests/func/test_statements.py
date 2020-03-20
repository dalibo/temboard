import json
from urllib2 import HTTPError

import pytest

from temboardagent.spc import connector

from test.temboard import temboard_request
from conftest import ENV


@pytest.fixture(scope="module")
def xsession():
    conn = connector(
        host=ENV["pg"]["socket_dir"],
        port=ENV["pg"]["port"],
        user=ENV["pg"]["user"],
        password=ENV["pg"]["password"],
        database="postgres",
    )
    conn.connect()
    conn.close()
    status, res = temboard_request(
        ENV["agent"]["ssl_cert_file"],
        method="POST",
        url="https://{host}:{port}/login".format(**ENV["agent"]),
        headers={"Content-type": "application/json"},
        data={
            "username": ENV["agent"]["user"],
            "password": ENV["agent"]["password"],
        },
    )
    assert status == 200
    return json.loads(res)["session"]


def test_statements(xsession):
    try:
        status, res = temboard_request(
            ENV["agent"]["ssl_cert_file"],
            method="GET",
            url="https://{host}:{port}/statements".format(**ENV["agent"]),
            headers={"X-Session": xsession},
        )
    except HTTPError as e:
        status = e.code
    assert status == 200
    assert json.loads(res) == {}
