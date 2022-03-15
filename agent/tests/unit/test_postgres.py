def test_postgres_connect(mocker):
    mocker.patch('temboardagent.postgres.connect', autospec=True)

    from temboardagent.postgres import Postgres

    postgres = Postgres(host='myhost')
    with postgres.connect() as conn:
        assert conn
    assert conn.close.called is True

    assert 'myhost' in repr(postgres)


def test_postgres_fetch_version(mocker):
    c = mocker.patch('temboardagent.postgres.connect', autospec=True)

    conn = c.return_value
    conn.server_version = 90400

    from temboardagent.postgres import Postgres

    postgres = Postgres(host='myhost')
    version = postgres.fetch_version()

    assert 90400 == version
    assert conn.close.called is True


def test_pickle():
    from pickle import dumps as pickle, loads as unpickle
    from temboardagent.postgres import Postgres

    orig = Postgres(host='myhost')
    copy = unpickle(pickle(orig))
    assert 'myhost' == copy.host
