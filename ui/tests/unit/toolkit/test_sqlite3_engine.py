import json
from datetime import datetime
from tempfile import NamedTemporaryFile

import pytest
from temboardui.toolkit.errors import StorageEngineError

DBNAME = ":memory:"


def execute(conn, query, args=()):
    with conn:
        c = conn.cursor()
        c.execute(query, args)
        return c.fetchall()


def test_bootstrap():
    from temboardui.toolkit.tasklist import sqlite3_engine

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    # Check tasks table exists
    execute(engine.conn, "SELECT * FROM tasks")


def test_insert():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    engine.insert(
        Task(
            id="bbbb",
            worker_name="foo",
            start_datetime=datetime(2020, 3, 22),
            status=1,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )

    # We have one row in the table
    assert (
        execute(engine.conn, "SELECT COUNT(id) FROM tasks")[0][0] == 1
    ), "Task not inserted."

    # Inserting Task with duplicated id raises KeyError
    with pytest.raises(KeyError):
        engine.insert(Task(id="bbbb"))

    # Check Task attributes
    r = execute(
        engine.conn,
        "SELECT worker_name, start_datetime, stop_datetime, status, output, "
        "options, redo_interval, expire FROM tasks WHERE id='bbbb'",
    )
    # worker_name
    assert r[0][0] == "foo"
    # start_datetime
    assert r[0][1] == 1584835200  # Epoch for 2020-03-22 00:00:00 UTC
    # stop_datetime
    assert r[0][2] == 0
    # status
    assert r[0][3] == 1
    # output
    assert r[0][4] == "bar"
    # options
    assert json.loads(r[0][5]) == {"foo": "bar"}
    # redo_interval
    assert r[0][6] == 42
    # expire
    assert r[0][7] == 90

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.insert(Task(id=1))

        assert "Could not insert task." in str(e.value)


def test_update():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    execute(engine.conn, "INSERT INTO tasks (id) VALUES ('aaaa')")
    engine.update(
        Task(
            id="aaaa",
            worker_name="foo",
            start_datetime=datetime(2020, 3, 22),
            status=1,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )

    # Check Task attributes
    r = execute(
        engine.conn,
        "SELECT worker_name, start_datetime, stop_datetime, status, output, "
        "options, redo_interval, expire FROM tasks WHERE id='aaaa'",
    )
    # worker_name
    assert r[0][0] == "foo"
    # start_datetime
    assert r[0][1] == 1584835200  # Epoch for 2020-03-22 00:00:00 UTC
    # stop_datetime
    assert r[0][2] == 0
    # status
    assert r[0][3] == 1
    # output
    assert r[0][4] == "bar"
    # options
    assert json.loads(r[0][5]) == {"foo": "bar"}
    # redo_interval
    assert r[0][6] == 42
    # expire
    assert r[0][7] == 90

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.update(Task(id=1))

        assert "Could not update task." in str(e.value)


def test_delete():
    from temboardui.toolkit.tasklist import sqlite3_engine

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    execute(engine.conn, "INSERT INTO tasks (id) VALUES ('cccc')")

    engine.delete("cccc")

    # We don't have row in the table
    assert (
        execute(engine.conn, "SELECT COUNT(id) FROM tasks")[0][0] == 0
    ), "Task not deleted."

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.delete(1)

        assert "Could not delete task with id=1" in str(e.value)


def test_get():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    engine.insert(
        Task(
            id="dddd",
            worker_name="foo",
            start_datetime=datetime(2020, 3, 22),
            status=1,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )

    task = engine.get("dddd")

    assert task.id == "dddd"
    assert task.worker_name == "foo"
    assert task.start_datetime == datetime(2020, 3, 22)
    assert task.stop_datetime is None
    assert task.status == 1
    assert task.output == "bar"
    assert task.options == {"foo": "bar"}
    assert task.redo_interval == 42
    assert task.expire == 90

    assert engine.get("not_found") is None

    # Update options with unvalid json data
    execute(engine.conn, "UPDATE tasks SET options='{\"ok\":1' WHERE id = 'dddd'")
    with pytest.raises(Exception) as e:
        engine.get("dddd")
    assert "Could not decode task options." in str(e.value)

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.get(1)

        assert "Could not get task with id=1" in str(e.value)


def test_list():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    engine.insert(
        Task(
            id="aaaaa",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=1,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="bbbbb",
            worker_name="worker_b",
            start_datetime=datetime(2020, 3, 23),
            status=1,
            output=None,
            options=dict(foo="bar"),
            redo_interval=2,
            expire=0,
        )
    )

    tasks = list(engine.list())

    assert tasks[0].id == "aaaaa"
    assert tasks[0].worker_name == "worker_a"
    assert tasks[0].start_datetime == datetime(2020, 3, 22)
    assert tasks[0].stop_datetime is None
    assert tasks[0].status == 1
    assert tasks[0].output == "bar"
    assert tasks[0].options == {"foo": "bar"}
    assert tasks[0].redo_interval == 42
    assert tasks[0].expire == 90

    assert tasks[1].id == "bbbbb"
    assert tasks[1].worker_name == "worker_b"
    assert tasks[1].start_datetime == datetime(2020, 3, 23)
    assert tasks[1].stop_datetime is None
    assert tasks[1].status == 1
    assert tasks[1].output is None
    assert tasks[1].options == {"foo": "bar"}
    assert tasks[1].redo_interval == 2
    assert tasks[1].expire == 0

    # Update options with unvalid json data
    execute(engine.conn, "UPDATE tasks SET options='{\"ok\":1' WHERE id = 'aaaaa'")
    assert len(list(engine.list())) == 1

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            list(engine.list())

        assert "Could not get task list." in str(e.value)


def test_exists():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    engine.insert(
        Task(
            id="aaaaa",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=1,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )

    assert engine.exists("aaaaa")
    assert not engine.exists("bbbbb")

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.exists(1)

        assert "Could not check that task with id=1 exists" in str(e.value)


def test_count_by_status():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    engine.insert(
        Task(
            id="aaaaa",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=1,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="bbbbb",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=2,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="ccccc",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=2,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )

    assert engine.count_by_status(1) == 1
    assert engine.count_by_status(2) == 2
    assert engine.count_by_status(1 | 2) == 3
    assert engine.count_by_status(4) == 0

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.count_by_status(1)

        assert "Could not count tasks with status & 1" in str(e.value)


def test_recover():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    st_doing = 1
    st_aborted = 2
    st_scheduled = 4
    st_default = 8

    engine.insert(
        Task(
            id="aaaaa",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=st_doing,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="bbbbb",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=st_scheduled,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )
    now = datetime.utcnow()
    engine.recover(st_doing, st_aborted, st_scheduled, st_default, now)
    t1 = engine.get("aaaaa")
    assert t1.status == st_default
    assert t1.stop_datetime.strftime("%Y-%m-%d %H:%M:%S") == now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )  # noqa
    t2 = engine.get("bbbbb")
    assert t2.status == st_default

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.recover(st_doing, st_aborted, st_scheduled, st_default, now)

        assert "Could not recover tasks." in str(e.value)


def test_list_to_do():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    st_aborted = 1
    st_default = 2
    st_done = 4

    engine.insert(
        Task(
            id="to_do",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 22),
            status=st_default,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=0,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="to_redo",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 20),
            status=st_done,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="not_to_do_1",
            worker_name="worker_a",
            start_datetime=datetime(1999, 1, 1),
            status=st_done,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=0,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="not_to_do_2",
            worker_name="worker_a",
            start_datetime=datetime(2999, 1, 1),
            status=st_default,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=0,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="not_to_redo",
            worker_name="worker_a",
            start_datetime=datetime(2999, 1, 1),
            status=st_done,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=42,
            expire=90,
        )
    )

    tasks = list(engine.list_to_do(st_default, datetime.utcnow()))
    assert len(tasks) == 1
    assert tasks[0].id == "to_do"
    assert tasks[0].worker_name == "worker_a"
    assert tasks[0].start_datetime == datetime(2020, 3, 22)
    assert tasks[0].stop_datetime is None
    assert tasks[0].status == st_default
    assert tasks[0].output == "bar"
    assert tasks[0].options == {"foo": "bar"}
    assert tasks[0].redo_interval == 0
    assert tasks[0].expire == 90

    tasks = list(
        engine.list_to_do(
            st_default | st_done | st_aborted, datetime.utcnow(), redo=True
        )
    )
    assert len(tasks) == 1
    assert tasks[0].id == "to_redo"

    # Update options with unvalid json data
    execute(engine.conn, "UPDATE tasks SET options='{\"ok\":1' WHERE id = 'to_do'")
    assert len(list(engine.list_to_do(st_default, datetime.utcnow()))) == 0

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            list(engine.list_to_do(st_default, datetime.utcnow()))

        assert "Could not get task list." in str(e.value)


def test_purge():
    from temboardui.toolkit.tasklist import sqlite3_engine
    from temboardui.toolkit.taskmanager import Task

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    st_aborted = 1
    st_default = 2
    st_done = 4

    engine.insert(
        Task(
            id="to_be_deleted",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 20),
            status=st_done,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=0,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="not_to_be_deleted",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 20),
            status=st_default,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=0,
            expire=90,
        )
    )
    engine.insert(
        Task(
            id="not_to_be_deleted_2",
            worker_name="worker_a",
            start_datetime=datetime(2020, 3, 20),
            status=st_done,
            output="bar",
            options=dict(foo="bar"),
            redo_interval=1,
            expire=90,
        )
    )

    engine.purge(st_aborted | st_done, datetime.utcnow())
    tasks = list(engine.list())
    assert len(tasks) == 2
    assert "not_to_be_deleted" in [t.id for t in tasks]
    assert "not_to_be_deleted_2" in [t.id for t in tasks]

    with NamedTemporaryFile() as f:
        engine = sqlite3_engine.TaskListSQLite3Engine(f.name)
        with pytest.raises(StorageEngineError) as e:
            engine.purge(st_aborted | st_done, datetime.utcnow())

        assert "Could not purge task list." in str(e.value)


def test_vacuum():
    from temboardui.toolkit.tasklist import sqlite3_engine

    engine = sqlite3_engine.TaskListSQLite3Engine(DBNAME)
    engine.bootstrap()

    # Just run vacuum without error
    engine.vacuum()
