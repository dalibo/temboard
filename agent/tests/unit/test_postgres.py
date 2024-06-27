def test_pickle():
    from pickle import dumps as pickle, loads as unpickle
    from temboardagent.postgres import Postgres

    orig = Postgres(host="myhost")
    copy = unpickle(pickle(orig))
    assert "myhost" == copy.host
