import pytest
from psycopg2 import errors as pgerrors


def test_inspect_schema_bootstrap(mocker):
    from temboardui.schema.migrator import Migrator

    migrator = Migrator()

    conn = mocker.MagicMock(name='conn')
    cur = conn.cursor.return_value.__enter__.return_value
    cur.execute.side_effect = pgerrors.UndefinedTable()
    current = migrator.inspect_current_version(conn)

    assert current is None
    assert migrator.current_version is None


def test_inspect_schema_existant(mocker):
    from temboardui.schema.migrator import Migrator

    migrator = Migrator()

    conn = mocker.MagicMock(name='conn')
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = ('000-init.sql', 'date')
    current = migrator.inspect_current_version(conn)

    assert '000-init.sql' == current
    assert '000-init.sql' == migrator.current_version


def test_inspect_schema_error(mocker):
    from temboardui.schema.migrator import Migrator

    migrator = Migrator()

    conn = mocker.MagicMock(name='conn')
    cur = conn.cursor.return_value.__enter__.return_value
    cur.execute.side_effect = pgerrors.IoError()

    with pytest.raises(pgerrors.IoError):
        migrator.inspect_current_version(conn)


def test_inspect_versions(mocker):
    glob = mocker.patch('temboardui.schema.migrator.glob')
    from temboardui.schema.migrator import Migrator

    migrator = Migrator()
    glob.return_value = [
        '000-init.sql',
        '002-v2.sql',
        '001-v1.sql',
    ]
    migrator.inspect_available_versions()

    assert 3 == len(migrator.missing_versions)
    assert '002-v2.sql' == migrator.target_version

    migrator.current_version = migrator.target_version
    assert not migrator.missing_versions


def test_apply_version(mocker):
    mod = 'temboardui.schema.migrator'
    open_ = mocker.patch(mod + '.open')
    open_.return_value = mocker.MagicMock()

    from temboardui.schema.migrator import Migrator

    migrator = Migrator()
    conn = mocker.MagicMock(name='conn')
    migrator.apply(conn, '000-init.sql')

    assert open_.called is True
    assert conn.cursor.called is True
