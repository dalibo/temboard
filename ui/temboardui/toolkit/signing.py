from base64 import b64decode, b64encode
from hashlib import sha256

from cryptography.hazmat.backends.openssl import backend as openssl_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from .errors import TemboardError
from .pycompat import quote_plus
from .utils import ensure_bytes


__all__ = [
    'InvalidSignature',
]


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
            "Missing headers for request signing: %s" % missing_headers)

    lines = [
        b"%s %s" % (method, ensure_bytes(quote_plus(path, safe='/'))),
        b"",
    ] + sorted([
        b"%s: %s" % (ensure_bytes(name), ensure_bytes(value))
        for name, value in
        canonicalized_headers.items()
    ])

    if b'POST' == method:
        h = sha256()
        h.update(body)
        lines += [
            b"",
            h.hexdigest().encode('ascii'),
        ]

    lines.append(b"")   # Final EOF

    return b"\n".join(lines)


def load_private_key(data):
    return serialization.load_pem_private_key(
        data, password=None, backend=openssl_backend)


def load_public_key(data):
    return serialization.load_pem_public_key(
        data, backend=openssl_backend)


HASH = hashes.SHA256()
PADDING = padding.PSS(
    mgf=padding.MGF1(HASH),
    salt_length=padding.PSS.MAX_LENGTH,
)


def sign_v1(private_key, payload):
    signature = private_key.sign(payload, PADDING, HASH)
    signature64 = b64encode(signature)
    return signature64.decode('ascii')


def verify_v1(public_key, signature, payload):
    signature_bin = b64decode(signature)
    public_key.verify(signature_bin, payload, PADDING, HASH)
