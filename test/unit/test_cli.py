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
    mocker.patch('temboardagent.cli.Application.read_dir', autospec=True)
    mocker.patch('temboardagent.cli.Application.apply_config', autospec=True)
    mocker.patch('temboardagent.cli.MergedConfiguration')
    from temboardagent.cli import Application, bootstrap

    app = Application()
    app.config.temboard.configfile = 'pouet'
    app.bootstrap(args=None, environ={})

    assert repr(app)

    app = bootstrap(args=None, environ={})

    assert app.apply_config.called is True


def test_apply_config_with_plugins(mocker):
    mod = 'temboardagent.cli.'
    mocker.patch(mod + 'Postgres', autospec=True)
    mocker.patch(mod + 'Application.setup_logging', autospec=True)
    cp = mocker.patch(mod + 'Application.create_plugins', autospec=True)
    mocker.patch(mod + 'Application.update_plugins', autospec=True)
    mocker.patch(mod + 'Application.purge_plugins', autospec=True)
    from temboardagent.cli import Application

    app = Application()
    app.config_sources = dict()
    app.config = mocker.Mock(name='config')
    app.config.postgresql = dict()
    cp.return_value = ['plugin']

    app.apply_config()

    assert app.postgres
    assert app.setup_logging.called is True
    assert app.update_plugins.called is True
    assert app.purge_plugins.called is True


def test_apply_config_without_plugins(mocker):
    mod = 'temboardagent.cli.'
    mocker.patch(mod + 'Postgres', autospec=True)
    mocker.patch(mod + 'Application.setup_logging', autospec=True)
    from temboardagent.cli import Application

    app = Application(with_plugins=False)
    app.config_sources = dict()
    app.config = mocker.Mock(name='config')
    app.config.postgresql = dict()

    app.apply_config()

    assert app.postgres
    assert app.setup_logging.called is True


def test_application_specs():
    from temboardagent.cli import Application

    app = Application()
    list(app.bootstrap_specs())
    list(app.core_specs())

    app = Application(with_plugins=None)
    specs = [str(s) for s in app.core_specs()]
    assert 'temboard_plugins' not in specs


def test_app_pickle():
    from pickle import dumps as pickle, loads as unpickle
    from temboardagent.cli import Application

    empty_generator = (x for x in [])
    orig = Application(specs=empty_generator)
    orig.config.update(dict(a=1))
    copy = unpickle(pickle(orig))
    assert [] == copy.specs
    assert copy.config


def test_read_file(mocker):
    from temboardagent.cli import Application, UserError

    app = Application()
    open_ = mocker.patch('temboardagent.cli.open', create=True)
    app.read_file(mocker.Mock(name='parser'), 'pouet.conf')

    open_.side_effect = IOError()
    with pytest.raises(UserError):
        app.read_file(mocker.Mock(name='parser'), 'pouet.conf')


def test_read_dir(mocker):
    rf = mocker.patch('temboardagent.cli.Application.read_file', autospec=True)
    isdir = mocker.patch('temboardagent.cli.os.path.isdir', autospec=True)
    glob = mocker.patch('temboardagent.cli.glob', autospec=True)

    from temboardagent.cli import Application

    app = Application()
    isdir.return_value = False
    app.read_dir(mocker.Mock(name='parser'), '/dev/null')

    isdir.return_value = True
    glob.return_value = ['pouet.conf.d/toto.conf']
    app.read_dir(mocker.Mock(name='parser'), 'pouet.conf.d')
    assert rf.called is True


def test_reload(mocker):
    m = 'temboardagent.cli.Application'
    mocker.patch(m + '.read_file', autospec=True)
    mocker.patch(m + '.read_dir', autospec=True)
    mocker.patch(m + '.apply_config', autospec=True)

    from temboardagent.cli import Application

    app = Application()
    app.config = mocker.Mock(name='config')
    app.config.temboard.configfile = 'pouet.conf'
    app.reload()


def test_fetch_plugin(mocker):
    iter_ep = mocker.patch('temboardagent.cli.pkg_resources.iter_entry_points')
    from temboardagent.cli import Application

    app = Application()
    ep = mocker.Mock(name='found')
    ep.name = 'found'
    ep.load.return_value = 'PLUGIN OBJECT'
    iter_ep.return_value = [ep]

    assert 'PLUGIN OBJECT' == app.fetch_plugin(['found'])


def test_fetch_failing(mocker):
    iter_ep = mocker.patch('temboardagent.cli.pkg_resources.iter_entry_points')
    from temboardagent.cli import Application, UserError

    app = Application()
    ep = mocker.Mock(name='ep')
    ep.load.side_effect = Exception('Pouet')
    iter_ep.return_value = [ep]

    with pytest.raises(UserError):
        app.fetch_plugin('myplugin')


def test_fetch_missing(mocker):
    iter_ep = mocker.patch('temboardagent.cli.pkg_resources.iter_entry_points')
    from temboardagent.cli import Application, UserError

    app = Application()
    iter_ep.return_value = []

    with pytest.raises(UserError):
        app.fetch_plugin('myplugin')


def test_create_plugins(mocker):
    mocker.patch(
        'temboardagent.cli.Application.fetch_plugin', autospec=True)
    from temboardagent.cli import Application

    app = Application()
    app.config = mocker.Mock(name='config')
    app.config.temboard.plugins = ['ng']
    app.create_plugins()

    assert 'ng' in app.plugins


def test_update_plugins(mocker):
    from temboardagent.cli import Application

    app = Application()

    unloadme = mocker.Mock(name='unloadme')
    old_plugins = dict(unloadme=unloadme)

    loadme = mocker.Mock(name='loadme')
    app.plugins = dict(loadme=loadme)

    app.update_plugins(old_plugins=old_plugins)

    assert loadme.load.called is True
    assert unloadme.unload.called is True


def test_purge_plugins():
    from temboardagent.cli import Application, MergedConfiguration

    app = Application()
    app.plugins = dict(destroyme=1, keepme=1)
    app.config = MergedConfiguration()
    app.config.update(dict(temboard=dict(plugins=['keepme'])))
    app.purge_plugins()
    assert 'destroyme' not in app.plugins


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
