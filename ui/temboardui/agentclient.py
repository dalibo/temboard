import json
import logging
from uuid import uuid4

from .toolkit.http import TemboardClient, format_date
from .toolkit.signing import canonicalize_request, sign_v1

logger = logging.getLogger(__name__)


class TemboardAgentClient(TemboardClient):
    @classmethod
    def factory(cls, config, host, port, username="temboard"):
        return cls(
            config.signing_key,
            host,
            port,
            ca_cert_file=config.temboard.ssl_ca_cert_file,
            username=username,
        )

    def __init__(self, signing_key, host, port, ca_cert_file=None, username="temboard"):
        super().__init__(host, port, ca_cert_file)
        self.signing_key = signing_key
        self.username = username

    def request(self, method, path, headers=None, body=None):
        hostport = f"{self.host}:{self.port}"
        headers = headers or {}

        headers.setdefault("Host", hostport)
        headers.setdefault("X-TemBoard-Date", format_date())
        headers.setdefault("X-TemBoard-Request-Id", str(uuid4()))
        headers.setdefault("X-TemBoard-User", self.username)

        # Preprocess body to sign it.
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
            headers["Content-Type"] = "application/json"

        if hasattr(body, "isnumeric"):  # Is it a unicode ?
            body = body.encode("utf-8")

        if "POST" == method:
            headers["Content-Length"] = str(len(body or b""))

        canonical_request = canonicalize_request(method, path, headers, body)
        if self.log_headers:
            logger.debug("Canonical request:\n%s", canonical_request.decode("utf-8"))
        signature = sign_v1(self.signing_key, canonical_request)
        headers["X-TemBoard-Signature"] = "v1:%s" % signature

        return super().request(method, path, headers, body)
