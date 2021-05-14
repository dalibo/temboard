import http.client as httpclient
import json
import os
import ssl
from urllib.parse import urlparse

import pytest
from selenium.webdriver import Remote
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


@pytest.fixture(scope='session')
def selenium():
    executor = os.environ.get('SELENIUM', 'http://localhost:4444') + '/wd/hub'
    driver = Remote(
        command_executor=executor,
        desired_capabilities=DesiredCapabilities.FIREFOX.copy(),
    )
    driver.implicitly_wait(3)
    yield driver
    driver.quit()


class HTTPClient:
    class Error(Exception):
        def __init__(self, response):
            self.response = response

    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, path, headers=None):
        url = urlparse(self.base_url + path)
        conn = httpclient.HTTPSConnection(
            url.hostname, url.port,
            timeout=5, context=ssl._create_unverified_context(),
        )
        headers = headers or {}
        conn.request('GET', url.path, None, headers)
        response = conn.getresponse()
        response.headers = dict(response.getheaders())
        response.body = response.read()
        if '/json' in response.headers.get('Content-Type', ''):
            response.json = json.loads(response.body)
        if response.status >= 400:
            raise self.Error(response)
        return response

    def post(self, path, body, headers=None):
        url = urlparse(self.base_url + path)
        conn = httpclient.HTTPSConnection(
            url.hostname, url.port,
            timeout=5, context=ssl._create_unverified_context(),
        )
        headers = headers or {}
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'
        conn.request('POST', url.path, body, headers)
        response = conn.getresponse()
        response.headers = dict(response.getheaders())
        response.body = response.read()
        if '/json' in response.headers.get('Content-Type', ''):
            response.json = json.loads(response.body)
        if response.status >= 400:
            raise self.Error(response)
        return response


@pytest.fixture()
def http(base_url):
    return HTTPClient(base_url)
