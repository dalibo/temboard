import pytest


@pytest.fixture(scope='session')
def selenium(session_capabilities):
    session_capabilities['acceptInsecureCerts'] = True
    return session_capabilities


def test_get(base_url, selenium):
    selenium.get(base_url + '/home')
