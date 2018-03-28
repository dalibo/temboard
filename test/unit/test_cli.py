from __future__ import unicode_literals

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


def test_bootstrap(mocker):
    mocker.patch('temboardagent.cli.Application.read_file', autospec=True)
    mocker.patch('temboardagent.cli.Application.create_plugins', autospec=True)
    mocker.patch('temboardagent.cli.MergedConfiguration')
    from temboardagent.cli import Application, bootstrap

    app = Application()
    app.config.temboard.configfile = 'pouet'
    app.plugins['toto'] = toto = mocker.Mock(name='toto')
    app.bootstrap(args=None, environ={})

    app = bootstrap(args=None, environ={})

    assert toto.load.called is True


def test_application_specs():
    from temboardagent.cli import Application

    app = Application()
    list(app.bootstrap_specs())
    list(app.core_specs())

    app = Application(with_plugins=None)
    specs = [str(s) for s in app.core_specs()]
    assert 'temboard_plugins' not in specs


def test_read_file(mocker):
    from temboardagent.cli import Application, UserError

    app = Application()
    open_ = mocker.patch('temboardagent.cli.open', create=True)
    app.read_file(mocker.Mock(name='parser'), 'pouet.conf')

    open_.side_effect = IOError()
    with pytest.raises(UserError):
        app.read_file(mocker.Mock(name='parser'), 'pouet.conf')


def test_reload(mocker):
    mocker.patch('temboardagent.cli.Application.read_file', autospec=True)
    mocker.patch('temboardagent.cli.load_legacy_plugins', autospec=True)

    from temboardagent.cli import Application

    app = Application()
    app.config = mocker.Mock(name='config')
    app.reload()


def test_fetch_plugin(mocker):
    iter_ep = mocker.patch('temboardagent.cli.iter_entry_points')
    from temboardagent.cli import Application

    app = Application()
    ep = mocker.Mock(name='found')
    ep.name = 'found'
    ep.load.return_value = 'PLUGIN OBJECT'
    iter_ep.return_value = [ep]

    assert 'PLUGIN OBJECT' == app.fetch_plugin(['found'])


def test_fetch_failing(mocker):
    iter_ep = mocker.patch('temboardagent.cli.iter_entry_points')
    from temboardagent.cli import Application, UserError

    app = Application()
    ep = mocker.Mock(name='ep')
    ep.load.side_effect = Exception('Pouet')
    iter_ep.return_value = [ep]

    with pytest.raises(UserError):
        app.fetch_plugin('myplugin')


def test_fetch_missing(mocker):
    iter_ep = mocker.patch('temboardagent.cli.iter_entry_points')
    from temboardagent.cli import Application, UserError

    app = Application()
    iter_ep.return_value = []

    with pytest.raises(UserError):
        app.fetch_plugin('myplugin')


def test_create_plugins(mocker):
    mocker.patch(
        'temboardagent.cli.Application.fetch_plugin', autospec=True)
    llp = mocker.patch('temboardagent.cli.load_legacy_plugins', autospec=True)
    from temboardagent.cli import Application

    app = Application()
    app.config = mocker.Mock(name='config')
    app.config.temboard.plugins = ['legacy', 'ng']

    llp.return_value = dict(legacy=dict())

    app.create_plugins()

    assert 'legacy' not in app.plugins
    assert 'legacy' in app.config.plugins
    assert 'ng' in app.plugins
    assert 'ng' not in app.config.plugins


def test_debug_arg():
    from argparse import ArgumentParser, SUPPRESS
    from temboardagent.cli import define_core_arguments

    parser = ArgumentParser(argument_default=SUPPRESS)
    define_core_arguments(parser)

    args = parser.parse_args([])
    assert 'logging_debug' not in args

    args = parser.parse_args(['--debug'])
    assert args.logging_debug is True

    args = parser.parse_args(['--debug', 'myplugin'])
    assert 'myplugin' == args.logging_debug


def test_debug_var():
    from temboardagent.cli import detect_debug_mode

    assert not detect_debug_mode(dict())
    assert not detect_debug_mode(dict(DEBUG=b'N'))

    env = dict(DEBUG=b'1')
    assert detect_debug_mode(env) is True
    assert b'__debug__' == env['TEMBOARD_LOGGING_DEBUG']

    env = dict(DEBUG=b'mymodule')
    assert detect_debug_mode(env)
    assert b'mymodule' == env['TEMBOARD_LOGGING_DEBUG']
