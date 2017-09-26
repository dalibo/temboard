import pytest


def test_big_main(mocker):
    pa = mocker.patch('temboardagent.register.agentRegisterOptions.parse_args')
    pa.return_value = (mocker.Mock(), mocker.Mock())
    mocker.patch('temboardagent.register.LazyConfiguration')

    from temboardagent.register import main

    with pytest.raises(SystemExit):
        main(argv=['--help'])
