import pytest


def test_big_main(mocker):
    mocker.patch('temboardagent.register.LazyConfiguration')

    from temboardagent.register import main

    with pytest.raises(SystemExit):
        main(argv=['--help'])
