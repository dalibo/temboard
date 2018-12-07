import pytest


def test_check_connectivity_ok(mocker):
    from temboardui.model import check_connectivity
    engine = mocker.Mock(name='engine')

    check_connectivity(engine)

    assert engine.connect().close.called is True


def test_check_connectivity_sleep(mocker):
    sleep = mocker.patch('temboardui.model.sleep')
    from temboardui.model import check_connectivity

    engine = mocker.Mock(name='engine')
    engine.connect.side_effect = [Exception(), mocker.Mock(name='connection')]

    check_connectivity(engine)

    assert sleep.called is True


def test_check_connectivity_fail(mocker):
    sleep = mocker.patch('temboardui.model.sleep')
    from temboardui.model import check_connectivity

    engine = mocker.Mock(name='engine')
    engine.connect.side_effect = Exception()

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
