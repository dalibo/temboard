import json
import logging
from uuid import uuid4

from .toolkit.http import TemboardClient, format_date
from .toolkit.signing import canonicalize_request, sign_v1


logger = logging.getLogger(__name__)


class TemboardAgentClient(TemboardClient):
    @classmethod
    def factory(cls, config, host, port, key=None, username='temboard'):
        return cls(
            config.signing_key,
            host, port,
            ca_cert_file=config.temboard.ssl_ca_cert_file,
            key=key,
            username=username,
        )

    def __init__(
            self, signing_key, host, port, ca_cert_file=None, key=None,
            username='temboard'):
        super(TemboardAgentClient, self).__init__(host, port, ca_cert_file)
        self.key = key  # Authentication key
        self.signing_key = signing_key
        self.username = username

    def request(self, method, path, headers=None, body=None):
        hostport = '%s:%s' % (self.host, self.port)
        headers = headers or {}

        headers.setdefault('Host', hostport)
        headers.setdefault('X-TemBoard-Date', format_date())
        headers.setdefault('X-TemBoard-Request-Id', str(uuid4()))
        headers.setdefault('X-TemBoard-User', self.username)

        if self.key:
            headers['X-TemBoard-Agent-Key'] = self.key

        # Preprocess body to sign it.
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'

        if hasattr(body, 'isnumeric'):  # Is it a unicode ?
            body = body.encode('utf-8')

        if 'POST' == method:
            headers['Content-Length'] = str(len(body or b''))

        canonical_request = canonicalize_request(method, path, headers, body)
        if self.log_headers:
            logger.debug(
                "Canonical request:\n%s", canonical_request.decode('utf-8'))
        signature = sign_v1(self.signing_key, canonical_request)
        headers['X-TemBoard-Signature'] = 'v1:%s' % signature

        return super(TemboardAgentClient, self).request(
            method, path, headers, body)
