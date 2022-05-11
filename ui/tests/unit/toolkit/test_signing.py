from textwrap import dedent

import pytest


@pytest.fixture(scope='module')
def headers():
    return {
            'host': '0.0.0.0:2345',
            'x-temboard-date': '20220511t095800z',
            'x-temboard-request-id': '2f3f3b60-a2a0-476c-a37a-5d63b5b10586',
            'x-temboard-user': 'alice',
        }


def test_canonicalize_request_get(headers):
    from temboardui.toolkit.signing import canonicalize_request

    data = canonicalize_request(
        method='get',
        path='/chemin',
        headers=headers,
    )

    wanted = dedent("""\
    GET /chemin

    host: 0.0.0.0:2345
    x-temboard-date: 20220511t095800z
    x-temboard-request-id: 2f3f3b60-a2a0-476c-a37a-5d63b5b10586
    x-temboard-user: alice
    """).encode('ascii')

    assert wanted == data


def test_canonicalize_request_get_missing_header():
    from temboardui.toolkit.signing import canonicalize_request, TemboardError

    with pytest.raises(TemboardError) as ei:
        canonicalize_request(
            method='get', path='/chemin',
            headers={},
        )

    message = str(ei.value)

    assert 'host' in message
    assert 'x-temboard-date' in message
    assert 'x-temboard-user' in message
    assert 'x-temboard-request-id' in message


def test_canonicalize_request_post(headers):
    from temboardui.toolkit.signing import canonicalize_request

    body = dedent("""\
    pouet
    """).encode('ascii')

    data = canonicalize_request(
        method='post', path='/chemin',
        headers={
            'Content-Type': 'text/plain',
            'Content-Length': str(len(body)),
            **headers,
        },
        body=body,
    )

    wanted = dedent("""\
    POST /chemin

    content-length: 6
    content-type: text/plain
    host: 0.0.0.0:2345
    x-temboard-date: 20220511t095800z
    x-temboard-request-id: 2f3f3b60-a2a0-476c-a37a-5d63b5b10586
    x-temboard-user: alice

    0e1b065625e33422c79539985c7c7c769fdff5417971b1259cc2b20ab18b7ddc
    """).encode('ascii').splitlines()

    assert wanted == data.splitlines()
