import http.client
import json
import logging
import ssl
import sys
from textwrap import dedent
from time import time

try:
    # python2
    from urllib2 import HTTPError
    from urlparse import urlparse
except Exception:
    # python3
    from urllib.error import HTTPError
    from urllib.parse import urlparse

from .toolkit.utils import ensure_bytes
from .toolkit.errors import TemboardError

try:
    ConnectionError = ConnectionError
except NameError:  # python2
    from socket import error as ConnectionError


logger = logging.getLogger(__name__)


def main():
    USAGE = dedent("""\
    A simple CLI client for temBoard agent.

    usage: python -m temboardui.temboardclient URL [BODY]

    Accepts body contents in stdin. temBoard agent accepts only JSON as body.

    """)

    logging.basicConfig(
        format="%(levelname)4.4s: %(message)s",
        level=logging.DEBUG,
    )

    try:
        url = urlparse(sys.argv[1])
    except IndexError:
        sys.stderr.write(USAGE)
        sys.exit(2)

    try:
        body = sys.argv[2]
    except IndexError:
        if sys.stdin.isatty():
            body = None
        else:
            logger.debug("Reading request body from STDIN.")
            body = sys.stdin.read()

    method = 'POST' if body else 'GET'

    client = TemboardAgentClient(url.hostname, url.port)
    pathinfo = url.path
    if url.query:
        pathinfo = "%s?%s" % (pathinfo, url.query)

    try:
        response = client.request(method, pathinfo, body=body)
        response.raise_for_status()
    except ConnectionError as e:
        logger.critical("%s", e)
        sys.exit(1)
    except TemboardAgentError as e:
        logger.error("%s", e)
        exit_code = 1
    else:
        exit_code = 0

    try:
        headers = response.headers.items()
    except AttributeError:  # python2
        headers = response.getheaders()
    for name, value in sorted(headers):
        sys.stderr.write("%s: %s\n" % (name, value))

    sys.stdout.write(response.read().decode('utf-8'))
    sys.exit(exit_code)


class TemboardAgentError(TemboardError):
    def __init__(self, response):
        self.response = response
        self._message = None

    @property
    def message(self):
        if not self._message:
            try:
                json = self.response.json()
                self._message = json['error']
            except Exception:
                self._message = self.response.reason
        return self._message

    def __str__(self):
        return '%s: %s' % (self.response.status, self.message)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self)


class TemboardAgentClient(object):
    ConnectionError = ConnectionError
    Error = TemboardAgentError

    @classmethod
    def factory(cls, config, host, port, key=None):
        return cls(
            host, port,
            ca_cert_file=config.temboard.ssl_ca_cert_file,
            key=key,
        )

    def __init__(self, host, port, ca_cert_file=None, key=None):
        """ If ca_cert_file is None, HTTPS connection is unverified. """
        self.host = host
        self.port = port
        self.ca_cert_file = ca_cert_file
        self.key = key  # Authentication key
        self._ssl_context = None

    def __repr__(self):
        return '<%s %s:%s %s>' % (
            self.__class__.__name__,
            self.host, self.port,
            'verified' if self.ca_cert_file else 'unverified',
        )

    @property
    def ssl_context(self):
        if self._ssl_context is None:
            self._ssl_context = ssl.create_default_context(
                cafile=self.ca_cert_file,
            )
            if self.ca_cert_file:
                self._ssl_context.verify_mode = ssl.CERT_REQUIRED
            else:

                self._ssl_context.check_hostname = False
                self._ssl_context.verify_mode = ssl.CERT_NONE
        return self._ssl_context

    def request(self, method, path, headers=None, body=None):
        fullurl = 'https://%s:%s%s' % (self.host, self.port, path)
        headers = headers or {}

        if self.key:
            headers['X-TemBoard-Agent-Key'] = self.key

        if body:
            headers['Content-Type'] = 'application/json'

        if hasattr(body, 'pop'):  # list or dict
            body = json.dumps(body)

        body = ensure_bytes(body)

        logger.debug("Requesting %s %s.", method, fullurl)
        conn = http.client.HTTPSConnection(
            self.host, self.port, context=self.ssl_context, timeout=30,
        )
        conn.response_class = TemboardAgentResponse
        start_time = time()
        conn.request(method, fullurl, body, headers)
        response = conn.getresponse()
        duration = time() - start_time
        response.path = path
        logger.debug(
            "Response from %s:%s in %.3fs: %s.",
            self.host, self.port, duration, response)
        return response

    def get(self, path, headers=None):
        return self.request('GET', path, headers)

    def post(self, path, body, headers=None):
        return self.request('POST', path, headers)


class TemboardAgentResponse(http.client.HTTPResponse):
    # Extensions to HTTPResponse, inspired by httpx

    def __str__(self):
        return '%s %s' % (self.status, self.reason)

    def __repr__(self):
        return '<%s %s %s -> %s %s %s>' % (
            self.__class__.__name__,
            self._method, self.path,
            self.status, self.reason,
            'closed' if self.isclosed() else 'opened',
        )

    def raise_for_status(self):
        if self.status >= 400:
            raise TemboardAgentError(self)
        elif self.status >= 300:
            raise HTTPError(self.status, self.reason)

    def json(self):
        return json.loads(self.read().decode('utf-8'))


if '__main__' == __name__:
    main()
