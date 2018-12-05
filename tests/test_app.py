from __future__ import unicode_literals

import pytest

from sampleproject.toolkit.app import BaseApplication


def cli(main):
    return BaseApplication(main=main)


def test_ok():
    @cli
    def main(app, argv, environ):
        assert 'TESTVALUE' in argv
        return 0xcafe

    with pytest.raises(SystemExit) as ei:
        main(argv=['TESTVALUE'])

    assert 0xcafe == ei.value.code


def test_missing_main():
    with pytest.raises(SystemExit):
        BaseApplication()()


def test_bdb_quit():
    from bdb import BdbQuit

    @cli
    def main(app, argv, environ):
        raise BdbQuit()

    with pytest.raises(SystemExit) as ei:
        main()

    assert 1 == ei.value.code


def test_interrupt():
    @cli
    def main(app, argv, environ):
        raise KeyboardInterrupt()

    with pytest.raises(SystemExit) as ei:
        main(argv=[])

    assert 1 == ei.value.code


def test_user_error():
    from sampleproject.toolkit.errors import UserError

    @cli
    def main(app, argv, environ):
        raise UserError('POUET', retcode=0xd0d0)

    with pytest.raises(SystemExit) as ei:
        main()

    assert 0xd0d0 == ei.value.code


def test_unhandled_error_prod():
    @cli
    def main(app, argv, environ):
        raise KeyError('name')

    with pytest.raises(SystemExit) as ei:
        main()

    assert 1 == ei.value.code


def test_unhandled_error_debug(mocker):
    pm = mocker.patch('sampleproject.toolkit.app.pdb.post_mortem')

    @cli
    def main(app, argv, environ):
        raise KeyError('name')

    with pytest.raises(SystemExit) as ei:
        main(environ=dict(DEBUG='y'))

    assert 1 == ei.value.code
    assert pm.called is True


def test_bootstrap(mocker):
    mod = 'sampleproject.toolkit.app'
    mocker.patch(mod + '.BaseApplication.read_file', autospec=True)
    mocker.patch(mod + '.BaseApplication.read_dir', autospec=True)
    mocker.patch(mod + '.BaseApplication.apply_config', autospec=True)
    mocker.patch(mod + '.MergedConfiguration')
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config.temboard.configfile = 'pouet'
    app.bootstrap(args=None, environ={})

    assert repr(app)


def test_apply_config_bad_logging(mocker):
    mod = 'sampleproject.toolkit.app.'
    sl = mocker.patch(mod + 'setup_logging', autospec=True)
    from sampleproject.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    app.config.logging = dict()
    sl.side_effect = Exception('pouet')

    with pytest.raises(UserError):
        app.apply_config()


def test_apply_config_with_plugins(mocker):
    mod = 'sampleproject.toolkit.app.'
    mocker.patch(mod + 'BaseApplication.setup_logging', autospec=True)
    cp = mocker.patch(mod + 'BaseApplication.create_plugins', autospec=True)
    mocker.patch(mod + 'BaseApplication.update_plugins', autospec=True)
    mocker.patch(mod + 'BaseApplication.purge_plugins', autospec=True)
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config_sources = dict()
    app.config = mocker.Mock(name='config')
    app.services.append(mocker.Mock(name='service'))
    cp.return_value = ['plugin']

    app.apply_config()

    assert app.setup_logging.called is True
    assert app.update_plugins.called is True
    assert app.purge_plugins.called is True


def test_apply_config_without_plugins(mocker):
    mod = 'sampleproject.toolkit.app.'
    mocker.patch(mod + 'BaseApplication.setup_logging', autospec=True)
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication(with_plugins=False)
    app.config_sources = dict()
    app.config = mocker.Mock(name='config')

    app.apply_config()

    assert app.setup_logging.called is True


def test_application_specs():
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    list(app.bootstrap_specs())
    list(app.core_specs())

    app = BaseApplication(with_plugins=None)
    specs = [str(s) for s in app.core_specs()]
    assert 'temboard_plugins' not in specs


def test_app_pickle():
    from pickle import dumps as pickle, loads as unpickle
    from sampleproject.toolkit.app import BaseApplication

    empty_generator = (x for x in [])
    orig = BaseApplication(specs=empty_generator)
    orig.config.update(dict(a=1))
    copy = unpickle(pickle(orig))
    assert [] == copy.specs
    assert copy.config


def test_read_file(mocker):
    from sampleproject.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    open_ = mocker.patch('sampleproject.toolkit.app.open', create=True)
    app.read_file(mocker.Mock(name='parser'), 'pouet.conf')

    open_.side_effect = IOError()
    with pytest.raises(UserError):
        app.read_file(mocker.Mock(name='parser'), 'pouet.conf')


def test_read_dir(mocker):
    mod = 'sampleproject.toolkit.app'
    rf = mocker.patch(mod + '.BaseApplication.read_file', autospec=True)
    isdir = mocker.patch(mod + '.os.path.isdir', autospec=True)
    glob = mocker.patch(mod + '.glob', autospec=True)

    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    isdir.return_value = False
    app.read_dir(mocker.Mock(name='parser'), '/dev/null')

    isdir.return_value = True
    glob.return_value = ['pouet.conf.d/toto.conf']
    app.read_dir(mocker.Mock(name='parser'), 'pouet.conf.d')
    assert rf.called is True


def test_reload(mocker):
    m = 'sampleproject.toolkit.app.BaseApplication'
    mocker.patch(m + '.read_file', autospec=True)
    mocker.patch(m + '.read_dir', autospec=True)
    mocker.patch(m + '.apply_config', autospec=True)

    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config = mocker.Mock(name='config')
    app.config.temboard.configfile = 'pouet.conf'
    app.reload()


def test_fetch_plugin(mocker):
    iter_ep = mocker.patch(
        'sampleproject.toolkit.app.pkg_resources.iter_entry_points')
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    ep = mocker.Mock(name='found')
    ep.name = 'found'
    ep.load.return_value = 'PLUGIN OBJECT'
    iter_ep.return_value = [ep]

    assert 'PLUGIN OBJECT' == app.fetch_plugin(['found'])


def test_fetch_failing(mocker):
    iter_ep = mocker.patch(
        'sampleproject.toolkit.app.pkg_resources.iter_entry_points')
    from sampleproject.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    ep = mocker.Mock(name='ep')
    ep.load.side_effect = Exception('Pouet')
    iter_ep.return_value = [ep]

    with pytest.raises(UserError):
        app.fetch_plugin('myplugin')


def test_fetch_missing(mocker):
    iter_ep = mocker.patch(
        'sampleproject.toolkit.app.pkg_resources.iter_entry_points')
    from sampleproject.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    iter_ep.return_value = []

    with pytest.raises(UserError):
        app.fetch_plugin('myplugin')


def test_create_plugins(mocker):
    mod = 'sampleproject.toolkit.app'
    mocker.patch(mod + '.refresh_distributions')
    mocker.patch(mod + '.refresh_pythonpath')
    mocker.patch(mod + '.BaseApplication.fetch_plugin', autospec=True)
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config = mocker.Mock(name='config')
    app.config.temboard.plugins = ['ng']
    app.create_plugins()

    assert 'ng' in app.plugins


def test_update_plugins(mocker):
    from sampleproject.toolkit.app import BaseApplication

    app = BaseApplication()

    unloadme = mocker.Mock(name='unloadme')
    old_plugins = dict(unloadme=unloadme)

    loadme = mocker.Mock(name='loadme')
    app.plugins = dict(loadme=loadme)

    app.update_plugins(old_plugins=old_plugins)

    assert loadme.load.called is True
    assert unloadme.unload.called is True


def test_purge_plugins():
    from sampleproject.toolkit.app import BaseApplication, MergedConfiguration

    app = BaseApplication()
    app.plugins = dict(destroyme=1, keepme=1)
    app.config = MergedConfiguration()
    app.config.update(dict(temboard=dict(plugins=['keepme'])))
    app.purge_plugins()
    assert 'destroyme' not in app.plugins


def test_debug_arg():
    from argparse import ArgumentParser, SUPPRESS
    from sampleproject.toolkit.app import define_core_arguments

    parser = ArgumentParser(argument_default=SUPPRESS)
    define_core_arguments(parser, appversion='1.0')

    args = parser.parse_args([])
    assert 'logging_debug' not in args

    args = parser.parse_args(['--debug'])
    assert args.logging_debug is True

    args = parser.parse_args(['--debug', 'myplugin'])
    assert 'myplugin' == args.logging_debug


def test_debug_var():
    from sampleproject.toolkit.app import detect_debug_mode

    assert not detect_debug_mode(dict())
    assert not detect_debug_mode(dict(DEBUG='N'))

    env = dict(DEBUG='1')
    assert detect_debug_mode(env) is True
    assert '__debug__' == env['TEMBOARD_LOGGING_DEBUG']

    env = dict(DEBUG='mymodule')
    assert detect_debug_mode(env)
    assert 'mymodule' == env['TEMBOARD_LOGGING_DEBUG']
