import logging
from hashlib import sha256

from .errors import TemboardError
from .utils import ensure_bytes


logger = logging.getLogger(__name__)


_REQUIRED_HEADERS = {
    'host',
    'x-temboard-date',
    'x-temboard-request-id',
    'x-temboard-user',
}

_REQUIRED_POST_HEADERS = _REQUIRED_HEADERS | {
    'content-type',
    'content-length',
}


def canonicalize_request(method, path, headers, body=b''):
    method = ensure_bytes(method.upper())
    if b'POST' == method:
        required = _REQUIRED_POST_HEADERS
    else:
        required = _REQUIRED_HEADERS

    canonicalized_headers = {
        name.lower(): value
        for name, value in
        headers.items()
        if name.lower() in required
    }

    missing_headers = required - set(canonicalized_headers)
    if missing_headers:
        missing_headers = ", ".join(sorted(missing_headers))
        raise TemboardError(
            f"Missing headers for request signing: {missing_headers}")

    lines = [
        b"%s %s" % (method, ensure_bytes(path)),
        b"",
        *sorted([
            b"%s: %s" % (ensure_bytes(name), ensure_bytes(value))
            for name, value in
            canonicalized_headers.items()
        ]),
    ]

    if b'POST' == method:
        h = sha256()
        h.update(body)
        lines += [
            b"",
            h.hexdigest().encode('ascii'),
        ]

    lines.append(b"")   # Final EOF

    logger.debug("Canonical request:\n%s", b"\n".join(lines).decode('utf-8'))
    return b"\n".join(lines)
