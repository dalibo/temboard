import pytest


def test_help():
    from temboardagent.scripts.agent import main

    with pytest.raises(SystemExit) as ei:
        main(argv=['--help'])

    assert 0 == ei.value.code


def test_options_specs():
    from temboardagent.scripts.agent import list_options_specs

    assert list(list_options_specs())


def test_big_main(mocker):
    mocker.patch('temboardagent.scripts.agent.bootstrap')
    mocker.patch('temboardagent.scripts.agent.daemonize')
    mocker.patch('temboardagent.scripts.agent.HTTPDService')
    mocker.patch('temboardagent.scripts.agent.purge_queue_dir')
    mocker.patch('temboardagent.scripts.agent.taskmanager.TaskManager')

    from temboardagent.scripts.agent import main

    with pytest.raises(SystemExit):
        main(argv=[])
