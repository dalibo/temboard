import pytest

from temboardui.toolkit.app import BaseApplication


def cli(main):
    return BaseApplication(main=main)


def test_ok():
    @cli
    def main(app, argv, environ):
        assert "TESTVALUE" in argv
        return 0xCAFE

    with pytest.raises(SystemExit) as ei:
        main(argv=["TESTVALUE"])

    assert 0xCAFE == ei.value.code


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
    from temboardui.toolkit.errors import UserError

    @cli
    def main(app, argv, environ):
        raise UserError("POUET", retcode=0xD0D0)

    with pytest.raises(SystemExit) as ei:
        main()

    assert 0xD0D0 == ei.value.code


def test_unhandled_error_prod():
    @cli
    def main(app, argv, environ):
        raise KeyError("name")

    with pytest.raises(SystemExit) as ei:
        main()

    assert 1 == ei.value.code


def test_unhandled_error_debug(mocker):
    pm = mocker.patch("temboardui.toolkit.app.pdb.post_mortem")

    @cli
    def main(app, argv, environ):
        raise KeyError("name")

    with pytest.raises(SystemExit) as ei:
        main(environ=dict(DEBUG="y"))

    assert 1 == ei.value.code
    assert pm.called is True


def test_bootstrap(caplog, mocker):
    mod = "temboardui.toolkit.app"
    fc = mocker.patch(mod + ".BaseApplication.find_config_file", autospec=True)
    mocker.patch(mod + ".BaseApplication.read_file", autospec=True)
    mocker.patch(mod + ".BaseApplication.read_dir", autospec=True)
    mocker.patch(mod + ".BaseApplication.apply_config", autospec=True)
    mocker.patch(mod + ".MergedConfiguration")
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    fc.return_value = "pouet"
    app.bootstrap(args=None, environ={})

    assert repr(app)

    # No config file is ok.
    caplog.clear()
    app.config.temboard.configfile = None
    fc.return_value = None
    app.bootstrap(args=None, environ={})
    assert caplog.records
    assert "No config file" in caplog.records[0].message


def test_find_config_file(mocker):
    mod = "temboardui.toolkit.app"
    exists = mocker.patch(mod + ".os.path.exists", autospec=True)

    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config.add_specs(app.list_stage1_specs())
    app.config.load()
    app.DEFAULT_CONFIGFILES = ["notfound", "/abs/notfound", "found", "/notsearched"]
    exists.side_effect = [False, False, True, Exception("Not reached")]
    assert "/found" in app.find_config_file()

    # No file found.
    exists.reset_mock()
    exists.side_effect = None
    exists.return_value = False
    assert app.find_config_file() is None


def test_apply_config_bad_logging(mocker):
    mod = "temboardui.toolkit.app."
    sl = mocker.patch(mod + "setup_logging", autospec=True)
    from temboardui.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    app.config.logging = dict()
    sl.side_effect = Exception("pouet")

    with pytest.raises(UserError):
        app.apply_config()


def test_apply_config_with_plugins(mocker):
    mod = "temboardui.toolkit.app."
    mocker.patch(mod + "BaseApplication.setup_logging", autospec=True)
    cp = mocker.patch(mod + "BaseApplication.create_plugins", autospec=True)
    mocker.patch(mod + "BaseApplication.load_plugins", autospec=True)
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config_sources = dict()
    app.config = mocker.Mock(name="config")
    app.services.append(mocker.Mock(name="service"))
    cp.return_value = ["plugin"]

    app.apply_config()

    assert app.setup_logging.called is True
    assert app.load_plugins.called is True


def test_apply_config_without_plugins(mocker):
    mod = "temboardui.toolkit.app."
    mocker.patch(mod + "BaseApplication.setup_logging", autospec=True)
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication(with_plugins=False)
    app.config_sources = dict()
    app.config = mocker.Mock(name="config")

    app.apply_config()

    assert app.setup_logging.called is True


def test_application_specs():
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    assert "temboard_plugins" in app.config_specs

    app = BaseApplication(with_plugins=None)
    assert "temboard_plugins" not in app.config_specs


def test_app_pickle():
    from pickle import dumps as pickle, loads as unpickle
    from temboardui.toolkit.app import BaseApplication

    empty_generator = (x for x in [])
    orig = BaseApplication(specs=empty_generator)
    orig.config.update(dict(a=1))
    copy = unpickle(pickle(orig))
    assert copy.config


def test_read_file(mocker):
    from temboardui.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    open_ = mocker.patch("temboardui.toolkit.app.open", create=True)
    app.read_file(mocker.Mock(name="parser"), "pouet.conf")

    open_.side_effect = IOError()
    with pytest.raises(UserError):
        app.read_file(mocker.Mock(name="parser"), "pouet.conf")


def test_read_dir(mocker):
    mod = "temboardui.toolkit.app"
    rf = mocker.patch(mod + ".BaseApplication.read_file", autospec=True)
    isdir = mocker.patch(mod + ".os.path.isdir", autospec=True)
    glob = mocker.patch(mod + ".glob", autospec=True)

    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    isdir.return_value = False
    app.read_dir(mocker.Mock(name="parser"), "/dev/null")

    isdir.return_value = True
    glob.return_value = ["pouet.conf.d/toto.conf"]
    app.read_dir(mocker.Mock(name="parser"), "pouet.conf.d")
    assert rf.called is True


def test_reload(mocker):
    m = "temboardui.toolkit.app.BaseApplication"
    mocker.patch(m + ".read_file", autospec=True)
    mocker.patch(m + ".read_dir", autospec=True)
    mocker.patch(m + ".apply_config", autospec=True)

    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config = mocker.MagicMock(name="config")
    app.config.temboard.configfile = "pouet.conf"
    app.reload()


def test_fetch_plugin(mocker):
    iter_ep = mocker.patch("temboardui.toolkit.app.pkg_resources.iter_entry_points")
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    ep = mocker.Mock(name="found")
    ep.name = "found"
    ep.load.return_value = "PLUGIN OBJECT"
    iter_ep.return_value = [ep]

    assert "PLUGIN OBJECT" == app.fetch_plugin(["found"])


def test_fetch_failing(mocker):
    iter_ep = mocker.patch("temboardui.toolkit.app.pkg_resources.iter_entry_points")
    from temboardui.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    ep = mocker.Mock(name="ep")
    ep.load.side_effect = Exception("Pouet")
    iter_ep.return_value = [ep]

    with pytest.raises(UserError):
        app.fetch_plugin("myplugin")


def test_fetch_missing(mocker):
    iter_ep = mocker.patch("temboardui.toolkit.app.pkg_resources.iter_entry_points")
    from temboardui.toolkit.app import BaseApplication, UserError

    app = BaseApplication()
    iter_ep.return_value = []

    with pytest.raises(UserError):
        app.fetch_plugin("myplugin")


def test_create_plugins(mocker):
    mod = "temboardui.toolkit.app"
    mocker.patch(mod + ".BaseApplication.fetch_plugin", autospec=True)
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    app.config = mocker.Mock(name="config")
    app.config.temboard.plugins = ["ng"]
    app.create_plugins()

    assert "ng" in app.plugins


def test_create_parser():
    from temboardui.toolkit.app import BaseApplication

    app = BaseApplication()
    parser = app.create_parser(add_help=False)
    assert "temboard" == parser.prog
    parser.add_argument("--help", action="help")


def test_debug_var():
    from temboardui.toolkit.app import detect_debug_mode

    assert not detect_debug_mode(dict())
    assert not detect_debug_mode(dict(DEBUG="N"))

    env = dict(DEBUG="1")
    assert detect_debug_mode(env) is True
    assert "__debug__" == env["TEMBOARD_LOGGING_DEBUG"]

    env = dict(DEBUG="mymodule")
    assert detect_debug_mode(env)
    assert "mymodule" == env["TEMBOARD_LOGGING_DEBUG"]
