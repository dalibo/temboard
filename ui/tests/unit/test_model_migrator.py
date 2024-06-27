import pytest


def test_inspect_schema_bootstrap(mocker):
    from temboardui.model.migrator import Migrator

    migrator = Migrator()

    conn = mocker.MagicMock(name="conn")
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = []
    current = migrator.inspect_current_version(conn)

    assert current is None
    assert migrator.current_version is None


def test_inspect_schema_inconsistent(mocker):
    from temboardui.model.migrator import Migrator

    migrator = Migrator()

    conn = mocker.MagicMock(name="conn")
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [("alembic_version",), ("sql_migration_log")]
    with pytest.raises(Exception) as ei:
        migrator.inspect_current_version(conn)

    # Assert plain exception, not a ValueError, etc.
    assert ei.type is Exception, ei.value


def test_inspect_schema_alembic(mocker):
    from temboardui.model.migrator import Migrator

    migrator = Migrator()
    migrator.versions = ["000_init", Migrator.LAST_ALEMBIC_VERSION, "003_drop-alembic"]

    conn = mocker.MagicMock(name="conn")
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [("alembic_version",)]
    current = migrator.inspect_current_version(conn)

    assert current.startswith("00")
    assert current != migrator.target_version


def test_inspect_schema_ok(mocker):
    from temboardui.model.migrator import Migrator

    migrator = Migrator()
    migrator.versions = ["000", "001", "002"]

    conn = mocker.MagicMock(name="conn")
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [("schema_migration_log",)]
    cur.fetchone.return_value = ("002",)

    current = migrator.inspect_current_version(conn)

    assert current == "002"
    assert current == migrator.target_version


def test_inspect_versions(mocker):
    glob = mocker.patch("temboardui.model.migrator.glob")
    from temboardui.model.migrator import Migrator

    migrator = Migrator()
    glob.return_value = ["000-init.sql", "002-v2.sql", "001-v1.sql"]
    migrator.inspect_available_versions()

    assert 3 == len(migrator.missing_versions)
    assert "002-v2.sql" == migrator.target_version

    migrator.current_version = migrator.target_version
    assert not migrator.missing_versions


def test_apply_version(mocker):
    mod = "temboardui.model.migrator"
    open_ = mocker.patch(mod + ".open")
    open_.return_value = mocker.MagicMock()

    from temboardui.model.migrator import Migrator

    migrator = Migrator()
    conn = mocker.MagicMock(name="conn")
    migrator.apply(conn, "000-init.sql")

    assert open_.called is True
    assert conn.cursor.called is True


def test_check():
    from temboardui.model.migrator import Migrator, UserError

    migrator = Migrator()

    # Uninitialized
    with pytest.raises(Exception) as ei:
        migrator.check()
    assert ei.type is Exception, ei.value

    # Not up to date
    migrator.current_version = None
    migrator.versions = ["000", "001"]

    with pytest.raises(UserError):
        migrator.check()

    # Up to date
    migrator.current_version = migrator.target_version
    migrator.check()
