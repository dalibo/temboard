import logging

from .toolkit.http import TemboardClient


logger = logging.getLogger(__name__)


class TemboardAgentClient(TemboardClient):
    @classmethod
    def factory(cls, config, host, port, key=None):
        return cls(
            host, port,
            ca_cert_file=config.temboard.ssl_ca_cert_file,
            key=key,
        )

    def __init__(self, host, port, ca_cert_file=None, key=None):
        super(TemboardAgentClient, self).__init__(host, port, ca_cert_file)
        self.key = key  # Authentication key

    def request(self, method, path, headers=None, body=None):
        headers = headers or {}

        if self.key:
            headers['X-TemBoard-Agent-Key'] = self.key

        return super(TemboardAgentClient, self).request(
            method, path, headers, body)
