import pytest


@pytest.fixture
def engine(mocker):
    engine = mocker.Mock(name='engine')
    conn = mocker.MagicMock(name='conn')
    engine.pool._invoke_creator.return_value = conn
    engine.conn = conn
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = ('PostgreSQL 15 Debian',)
    engine.cur = cur
    return engine


def test_check_connectivity_ok(engine, mocker):
    sleep = mocker.patch('temboardui.model.sleep')
    sleep.side_effect = Exception("Must not sleep")
    from temboardui.model import check_connectivity

    check_connectivity(engine)

    assert engine.conn.close.called is True


def test_check_connectivity_sleep(engine, mocker):
    sleep = mocker.patch('temboardui.model.sleep')
    from temboardui.model import check_connectivity

    engine.pool._invoke_creator.side_effect = [
        Exception(), engine.conn,
    ]

    check_connectivity(engine)

    assert sleep.called is True


def test_check_connectivity_fail(engine, mocker):
    sleep = mocker.patch('temboardui.model.sleep')
    from temboardui.model import check_connectivity

    engine.pool._invoke_creator.side_effect = Exception()

    with pytest.raises(Exception):
        check_connectivity(engine)

    assert sleep.called is True


def test_configure(mocker):
    mod = 'temboardui.model'
    Session = mocker.patch(mod + '.Session')
    check = mocker.patch(mod + '.check_connectivity')

    from temboardui.model import configure

    configure(dsn='sqlite://')  # LOL
    assert Session.configure.called is True
    assert check.called is True

    check.side_effect = Exception()
    with pytest.raises(SystemExit):
        config = dict(host='h', port=5432, user='u', password='X', dbname='db')
        configure(dsn=config)
