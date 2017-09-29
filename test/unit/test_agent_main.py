import pytest


def test_help(mocker):
    from temboardagent.scripts.agent import main

    with pytest.raises(SystemExit):
        main(argv=['--help'])


def test_big_main(mocker):
    mocker.patch('temboardagent.scripts.agent.load_configuration')
    mocker.patch('temboardagent.scripts.agent.daemonize')
    mocker.patch('temboardagent.scripts.agent.httpd_run')
    mocker.patch('temboardagent.scripts.agent.Process')
    mocker.patch('temboardagent.scripts.agent.purge_queue_dir')

    from temboardagent.scripts.agent import main

    with pytest.raises(SystemExit):
        main(argv=[])
