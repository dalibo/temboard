from contextlib import contextmanager
import json
import re
import time

import pytest

from temboardagent.spc import connector

from test.temboard import temboard_request, urllib2

ENV = {}

@pytest.fixture(scope="module")
def xsession(env):
    ENV.update(env)
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
def extension_enabled(env):
    ENV.update(env)
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
    except urllib2.HTTPError as e:
        status = e.code
    assert status == 404


def test_statements(xsession, extension_enabled):
    with conn() as cnx:
        cnx.execute("SELECT version()")
        row, = cnx.get_rows()
        m = re.match(r"PostgreSQL (\d+\.?\d*)", row["version"])
        assert m
        pg_version = tuple(
            int(x) for x in m.group(1).split(".")
        )

    def get_statements():
        try:
            status, res = temboard_request(
                ENV["agent"]["ssl_cert_file"],
                method="GET",
                url="https://{host}:{port}/statements".format(**ENV["agent"]),
                headers={"X-Session": xsession},
            )
        except urllib2.HTTPError as e:
            status = e.code
        assert status == 200
        return json.loads(res)

    result = get_statements()
    snapshot_datetime = time.strptime(
        result["snapshot_datetime"], "%Y-%m-%d %H:%M:%S +0000"
    )
    data = result["data"]
    assert data
    expected_keys = {
            "blk_read_time",
            "blk_write_time",
            "calls",
            "datname",
            "dbid",
            "local_blks_dirtied",
            "local_blks_hit",
            "local_blks_read",
            "local_blks_written",
            "query",
            "queryid",
            "rolname",
            "rows",
            "shared_blks_dirtied",
            "shared_blks_hit",
            "shared_blks_read",
            "shared_blks_written",
            "temp_blks_read",
            "temp_blks_written",
            "userid",
    }
    if pg_version >= (13,):
        expected_keys = expected_keys | {
            'max_exec_time',
            'max_plan_time',
            'mean_exec_time',
            'mean_plan_time',
            'min_exec_time',
            'min_plan_time',
            'plans',
            'rolname',
            'rows',
            'stddev_exec_time',
            'stddev_plan_time',
            'total_exec_time',
            'total_plan_time',
            'wal_bytes',
            'wal_fpi',
            'wal_records',
        }
    else:
        expected_keys = expected_keys | {
            "max_time",
            "mean_time",
            "min_time",
            "stddev_time",
            "total_time",
        }
    if pg_version >= (14,):
        expected_keys.add('toplevel')

    # This assert let pytest shows the diff between expected and returned.
    assert set(data[0]) == expected_keys
    assert all(set(d) == expected_keys for d in data)
    assert "temboard" in {d["rolname"] for d in data}
    assert "postgres" in {d["datname"] for d in data}
    queries = [d["query"] for d in data]
    assert "CREATE EXTENSION pg_stat_statements" in queries

    query = "SELECT 1+1"
    with conn() as cnx:
        cnx.execute(query)

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
    assert "temboard" in {d["rolname"] for d in new_data}
    assert "postgres" in {d["datname"] for d in new_data}
    new_queries = [d["query"] for d in new_data]

    stmt_query = "SELECT $1+$2" if pg_version > (10,) else "SELECT ?+?"
    assert stmt_query in new_queries
    calls = [d["calls"] for d in new_data if d["query"] == stmt_query][0]
    assert calls == 1

    with conn() as cnx:
        cnx.execute(query)

    # sleep 1s to get a different snapshot timestamp
    time.sleep(1)

    result = get_statements()
    third_data = result["data"]
    calls = [d["calls"] for d in third_data if d["query"] == stmt_query][0]
    assert calls == 2
