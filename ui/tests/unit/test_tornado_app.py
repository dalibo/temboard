from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture(scope="session")
def executor():
    yield ThreadPoolExecutor(2)


def test_app_configure(mocker):
    from temboardui.web.tornado import WebApplication

    app = WebApplication()
    app.configure(debug=True)
    assert app.settings["autoreload"] is True
