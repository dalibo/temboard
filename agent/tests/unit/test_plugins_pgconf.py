import pytest


def test_human_to_number():
    from temboardagent.plugins.pgconf.functions import human_to_number

    assert 2 == human_to_number("2ms", "ms")
    with pytest.raises(Exception):
        human_to_number("0.2ms", "ms")
    assert 0.2 == human_to_number("0.2ms", "ms", float)
    assert 2.2 == human_to_number("2200us", "ms")
