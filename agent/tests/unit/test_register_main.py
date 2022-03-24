import pytest


def test_big_main(mocker):
    from temboardagent.scripts.register import main

    with pytest.raises(SystemExit):
        main(argv=['--help'], environ={})
