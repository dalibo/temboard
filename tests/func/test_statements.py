from contextlib import contextmanager
import json
from urllib2 import HTTPError
import time

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


@contextmanager
def conn():
    cnx = connector(
        host=ENV["pg"]["socket_dir"],
        port=ENV["pg"]["port"],
        user=ENV["pg"]["user"],
        password=ENV["pg"]["password"],
        database="postgres",
    )
    cnx.connect()
    try:
        yield cnx
    finally:
        cnx.close()


@pytest.fixture(scope="function")
def extension_enabled():
    with conn() as cnx:
        cnx.execute("CREATE EXTENSION pg_stat_statements")
    yield
    with conn() as cnx:
        cnx.execute("DROP EXTENSION pg_stat_statements")


def test_statements_not_enabled(xsession):
    try:
        status, res = temboard_request(
            ENV["agent"]["ssl_cert_file"],
            method="GET",
            url="https://{host}:{port}/statements".format(**ENV["agent"]),
            headers={"X-Session": xsession},
        )
    except HTTPError as e:
        status = e.code
    assert status == 404


def test_statements(xsession, extension_enabled):
    with conn() as cnx:
        cnx.execute("SELECT version()")
        row, = cnx.get_rows()
        pg_version = tuple(
            int(x) for x in row["version"].split(" ", 2)[1].split(".")
        )

    def get_statements():
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
        return json.loads(res)

    result = get_statements()
    snapshot_datetime = time.strptime(
        result["snapshot_datetime"], "%Y-%m-%d %H:%M:%S +0000"
    )
    data = result["data"]
    assert data
    expected_keys = set(
        [
            u"blk_read_time",
            u"blk_write_time",
            u"calls",
            u"dbid",
            u"local_blks_dirtied",
            u"local_blks_hit",
            u"local_blks_read",
            u"local_blks_written",
            u"max_time",
            u"mean_time",
            u"min_time",
            u"query",
            u"queryid",
            u"rows",
            u"shared_blks_dirtied",
            u"shared_blks_hit",
            u"shared_blks_read",
            u"shared_blks_written",
            u"stddev_time",
            u"temp_blks_read",
            u"temp_blks_written",
            u"total_time",
            u"userid",
        ]
    )
    assert all(set(d) == expected_keys for d in data)
    queries = [d["query"] for d in data]
    assert "CREATE EXTENSION pg_stat_statements" in queries

    with conn() as cnx:
        cnx.execute("SELECT 1+1")

    # sleep 1s to get a different snapshot timestamp
    time.sleep(1)

    result = get_statements()
    new_snapshot_datetime = time.strptime(
        result["snapshot_datetime"], "%Y-%m-%d %H:%M:%S +0000"
    )
    assert new_snapshot_datetime > snapshot_datetime
    new_data = result["data"]
    assert new_data
    assert all(set(d) == expected_keys for d in new_data)
    assert len(new_data) != len(data)
    new_queries = [d["query"] for d in new_data]
    assert "SELECT pg_stat_statements_reset()" in new_queries
    if pg_version > (10,):
        assert "SELECT $1+$2" in new_queries
    else:
        assert "SELECT ?+?" in new_queries
