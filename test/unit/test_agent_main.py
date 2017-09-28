import pytest


def test_help(mocker):
    from temboardagent.agent import main

    with pytest.raises(SystemExit):
        main(argv=['--help'])


def test_big_main(mocker):
    mocker.patch('temboardagent.agent.load_configuration')
    mocker.patch('temboardagent.agent.daemonize')
    mocker.patch('temboardagent.agent.httpd_run')
    mocker.patch('temboardagent.agent.Process')
    mocker.patch('temboardagent.agent.purge_queue_dir')

    from temboardagent.agent import main

    with pytest.raises(SystemExit):
        main(argv=[])
