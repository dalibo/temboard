def test_postgres_fetch_version(mocker):
    c = mocker.patch('temboardagent.postgres.connect', autospec=True)

    conn = c.return_value
    conn.__enter__.return_value = conn
    conn.server_version = 90400

    from temboardagent.postgres import Postgres

    postgres = Postgres(host='myhost')
    version = postgres.fetch_version()

    assert 90400 == version


def test_pickle():
    from pickle import dumps as pickle, loads as unpickle
    from temboardagent.postgres import Postgres

    orig = Postgres(host='myhost')
    copy = unpickle(pickle(orig))
    assert 'myhost' == copy.host
