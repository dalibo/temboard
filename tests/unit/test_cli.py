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
