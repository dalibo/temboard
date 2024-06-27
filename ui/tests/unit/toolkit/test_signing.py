from base64 import b64decode
from textwrap import dedent

import pytest


@pytest.fixture(scope="module")
def headers():
    return {
        "host": "0.0.0.0:2345",
        "x-temboard-date": "20220511t095800z",
        "x-temboard-request-id": "2f3f3b60-a2a0-476c-a37a-5d63b5b10586",
        "x-temboard-user": "alice",
    }


def test_canonicalize_request_get(headers):
    from temboardui.toolkit.signing import canonicalize_request

    data = canonicalize_request(method="get", path="/chemin/toto+titi", headers=headers)

    wanted = dedent("""\
    GET /chemin/toto%2Btiti

    host: 0.0.0.0:2345
    x-temboard-date: 20220511t095800z
    x-temboard-request-id: 2f3f3b60-a2a0-476c-a37a-5d63b5b10586
    x-temboard-user: alice
    """).encode("ascii")

    assert wanted == data


def test_canonicalize_request_get_missing_header():
    from temboardui.toolkit.signing import TemboardError, canonicalize_request

    with pytest.raises(TemboardError) as ei:
        canonicalize_request(method="get", path="/chemin", headers={})

    message = str(ei.value)

    assert "host" in message
    assert "x-temboard-date" in message
    assert "x-temboard-user" in message
    assert "x-temboard-request-id" in message


def test_canonicalize_request_post(headers):
    from temboardui.toolkit.signing import canonicalize_request

    body = dedent("""\
    pouet
    """).encode("ascii")

    data = canonicalize_request(
        method="post",
        path="/chemin",
        headers=dict(
            {"Content-Type": "text/plain", "Content-Length": str(len(body))}, **headers
        ),
        body=body,
    )

    wanted = (
        dedent("""\
    POST /chemin

    content-length: 6
    content-type: text/plain
    host: 0.0.0.0:2345
    x-temboard-date: 20220511t095800z
    x-temboard-request-id: 2f3f3b60-a2a0-476c-a37a-5d63b5b10586
    x-temboard-user: alice

    0e1b065625e33422c79539985c7c7c769fdff5417971b1259cc2b20ab18b7ddc
    """)
        .encode("ascii")
        .splitlines()
    )

    assert wanted == data.splitlines()


RSA_PRIVATE_KEY = b"""\
-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
"""

RSA_PUBLIC_KEY = b"""\
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA4TVNVsTR3IaL9hdV69XY
6FEFnZpxfdJ5HuKtku+Gy+ezw4swTNLolSXn1OYDlLd688aE0p3xER+dtim5bWxj
p2iTnN2hS8w6hPMA3o5noBG1UWJy5jjKeVF40h92MAB6KU4SA84IJNz+zBQTIFkx
AqRaOJUPqyJwXeHhkiH3p5zuPHw+FPZZkNcmL4FuoPjZ5KGvPalUvmUM7HZevSdf
4Ycsn5xEHB8mutpwheNhRJDRuUfzZxoj6Iru7hPxWOSrQdgkIxYymZV0YrRGB0OI
AV5Go1MwWCAyK8D55JO9F3fZMwyVbSHAdOEcvCVqf8YBrjT3BzvgxM1qDx+k5Mlb
3RcMED9EXNGwKUHKxsc9jEFunNeM6t8mpndki2gdxrmZsovQ2MDAmGcFNTffSO5h
S5hm4nw44Vv2SG7FBOp29WmGbOdBnNRwAt1f5VvvyYLwwAX3bk8ljIYplMBWJN5D
sl0kT9YPYphbWtWESLX9X/LgpgD7t299m4Fi0OEyamL0jF4pRgvTha3vUIEtcgaJ
3WNGVFQRBHgu8lIUmI6hO7swCMnIG+CcjCRo0ez/e0JyK6ONVFuuwt38FSam+Nrk
vDqvhmKaNFwJpkWuSW3p+j5fjWVsf39arIodLU4XxNr32LaqKncld24bRYhg35CG
/saax0girQznwhje0AH0tLMCAwEAAQ==
-----END PUBLIC KEY-----
"""


def test_signing():
    from temboardui.toolkit.signing import HASH, PADDING, load_private_key, sign_v1

    key = load_private_key(RSA_PRIVATE_KEY)

    payload = b"payload"
    signature = sign_v1(key, payload)

    assert 684 == len(signature)

    signature_bin = b64decode(signature)

    assert 512 == len(signature_bin)

    public_key = key.public_key()
    public_key.verify(signature_bin, payload, PADDING, HASH)

    corrupted_signature_bin = signature_bin + b"x"
    with pytest.raises(Exception):
        public_key.verify(corrupted_signature_bin, payload, PADDING, HASH)


def test_verifying():
    from temboardui.toolkit.signing import InvalidSignature, load_public_key, verify_v1

    payload = b"payload"
    signature = (
        b"hTeEP+iUWllMWISqbXErKglCqy9vLpKzCnIeHfm7CbvDu+oNmND1l4NcLhap4HSqMg1Z"
        b"Jwdtf7MACWz7p1Y3zpRajjjlRtaj+MojKBUGkz0MR4ciKkiRlmR7eW4wVOSXfr3vFPK1"
        b"uI0sySj5uDyuLzViGzTHyS7M1fVawkecMvzjt43f736H6QbRJLwMO1+1uVgXxcAwyH+q"
        b"G5rLIG0YDUKpA4wKsNDJ/f8ZjtlamJJjtreOslh9PlOWDxRIGzCSitBrHS+9bKwr5G52"
        b"sSycAx+f9+sGYCoKhIhZuPK9bDmpjyv/5eHZ0v43FufOQw1WV5dWENlo4NgQb3wbTyWB"
        b"i8YZEMZ1rMGcTzEeCo32CaZmF6zULJzcM4KYMEN1X48ED6SlTJOHABGEkzelDNl66hgR"
        b"ftSi8enovIgHgtIu/E8OCIAz2yQ9yeCsHBpPcis0GFGjKiotQjhMlm9KkTl+pOfPhpzY"
        b"f3T1jGVQ1DkNGXJc10d+tKv+Vl26H3Z56B8gnjAzE4p4aLyxg8PQLKz/ugm4vQ9z3GSB"
        b"wIpIc581pKP/dQ3Fmcn8+Kx7UaRTEh5n+OMcdDlkyzvP/1pUevHlaQE874BlQbPKV7Sl"
        b"us4kTb/8bytFjX6m4gx7t08Su+OIj9ibuLa7Vs9jjFCQBzv4s0nJabORpY6p4hZ7qcq3"
        b"N4Y="
    )

    key = load_public_key(RSA_PUBLIC_KEY)
    with pytest.raises(InvalidSignature):
        verify_v1(key, b"x" + signature, payload)

    with pytest.raises(InvalidSignature):
        verify_v1(key, signature, payload + b"x")

    verify_v1(key, signature, payload)
