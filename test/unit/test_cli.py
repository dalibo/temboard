import pytest


def test_ok():
    from temboardagent.cli import cli

    @cli
    def main(argv, environ):
        assert 'TESTVALUE' in argv
        return 0xcafe

    with pytest.raises(SystemExit) as ei:
        main(argv=['TESTVALUE'])

    assert 0xcafe == ei.value.code


def test_bdb_quit():
    from temboardagent.cli import cli
    from bdb import BdbQuit

    @cli
    def main(argv, environ):
        raise BdbQuit()

    with pytest.raises(SystemExit) as ei:
        main()

    assert 1 == ei.value.code


def test_interrupt():
    from temboardagent.cli import cli

    @cli
    def main(argv, environ):
        raise KeyboardInterrupt()

    with pytest.raises(SystemExit) as ei:
        main(argv=[])

    assert 1 == ei.value.code


def test_user_error():
    from temboardagent.cli import cli
    from temboardagent.errors import UserError

    @cli
    def main(argv, environ):
        raise UserError('POUET', retcode=0xd0d0)

    with pytest.raises(SystemExit) as ei:
        main()

    assert 0xd0d0 == ei.value.code


def test_unhandled_error_prod():
    from temboardagent.cli import cli

    @cli
    def main(argv, environ):
        raise KeyError('name')

    with pytest.raises(SystemExit) as ei:
        main()

    assert 1 == ei.value.code


def test_unhandled_error_debug(mocker):
    from temboardagent.cli import cli
    pm = mocker.patch('temboardagent.cli.pdb.post_mortem')

    @cli
    def main(argv, environ):
        raise KeyError('name')

    with pytest.raises(SystemExit) as ei:
        main(environ=dict(DEBUG='y'))

    assert 1 == ei.value.code
    assert pm.called is True
