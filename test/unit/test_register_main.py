import pytest


def test_big_main(mocker):
    mocker.patch('temboardagent.scripts.register.bootstrap')

    from temboardagent.scripts.register import main

    with pytest.raises(SystemExit):
        main(argv=['--help'])
