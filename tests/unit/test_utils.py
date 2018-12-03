import pytest


def test_check_connectivity_ok(mocker):
    from temboardui.utils import check_sqlalchemy_connectivity
    engine = mocker.Mock(name='engine')

    check_sqlalchemy_connectivity(engine)

    assert engine.connect().close.called is True


def test_check_connectivity_sleep(mocker):
    sleep = mocker.patch('temboardui.utils.sleep')
    from temboardui.utils import check_sqlalchemy_connectivity

    engine = mocker.Mock(name='engine')
    engine.connect.side_effect = [Exception(), mocker.Mock(name='connection')]

    check_sqlalchemy_connectivity(engine)

    assert sleep.called is True


def test_check_connectivity_fail(mocker):
    sleep = mocker.patch('temboardui.utils.sleep')
    from temboardui.utils import check_sqlalchemy_connectivity

    engine = mocker.Mock(name='engine')
    engine.connect.side_effect = Exception()

    with pytest.raises(Exception):
        check_sqlalchemy_connectivity(engine)

    assert sleep.called is True
