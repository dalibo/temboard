import pytest


def test_big_main(mocker):
    pa = mocker.patch('temboardagent.agent.temboardOptions.parse_args')
    pa.return_value = (mocker.Mock(), mocker.Mock())
    mocker.patch('temboardagent.agent.Configuration')
    mocker.patch('temboardagent.agent.daemonize')
    mocker.patch('temboardagent.agent.logging.config.dictConfig')
    mocker.patch('temboardagent.agent.httpd_run')
    mocker.patch('temboardagent.agent.load_plugins_configurations')
    mocker.patch('temboardagent.agent.Process')
    mocker.patch('temboardagent.agent.purge_queue_dir')

    from temboardagent.agent import main

    with pytest.raises(SystemExit):
        main(argv=[])
