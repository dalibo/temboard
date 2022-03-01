import json
import logging
import ssl
try:
    # python2
    from urlparse import urlparse
    from httplib import HTTPSConnection
except Exception:
    # python3
    from urllib.parse import urlparse
    from http.client import HTTPSConnection

import pytest


logger = logging.getLogger(__name__)


class HTTPClient:
    class Error(Exception):
        def __init__(self, response):
            self.response = response

    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, path, headers=None):
        url = urlparse(self.base_url + path)
        conn = HTTPSConnection(
            url.hostname, url.port,
            timeout=5, context=ssl._create_unverified_context(),
        )
        headers = headers or {}
        conn.request('GET', url.path, None, headers)
        response = conn.getresponse()
        response.headers = dict(response.getheaders())
        response.body = response.read()
        if hasattr(response.body, 'decode'):
            response.body = response.body.decode('utf-8')
        if '/json' in response.headers.get('content-type', '') or \
           '/json' in response.headers.get('Content-Type', ''):
            response.json = json.loads(response.body)
        if response.status >= 400:
            raise self.Error(response)
        return response

    def post(self, path, body, headers=None):
        url = urlparse(self.base_url + path)
        conn = HTTPSConnection(
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
        if hasattr(response.body, 'decode'):
            response.body = response.body.decode('utf-8')
        if '/json' in response.headers.get('content-type', '') or \
           '/json' in response.headers.get('Content-Type', ''):
            response.json = json.loads(response.body)
        if response.status >= 400:
            raise self.Error(response)
        return response


@pytest.fixture()
def http(base_url):
    return HTTPClient(base_url)
