def test_dict_factory():
    from temboardtoolkit.utils import dict_factory

    my = dict_factory()
    assert isinstance(my, dict)
    assert 0 == len(my)

    my = dict_factory(dict(a=True))
    assert isinstance(my, dict)
    assert 1 == len(my)
    assert my["a"] is True

    my = dict_factory([("a", True)])
    assert isinstance(my, dict)
    assert 1 == len(my)
    assert my["a"] is True

    original = dict(a=True)
    my = dict_factory(original)
    original["a"] = False
    assert my["a"] is False


def test_dotdict():
    from temboardtoolkit.utils import DotDict

    my = DotDict(dict(a=1, b=dict(c=2)))

    assert 1 == my.a
    assert 1 == my["a"]
    assert 2 == my.b.c
    assert 2 == my["b"].c

    keys = list(iter(my))
    assert "a" in keys
    assert "b" in keys

    my.a = 3
    my.b.c = 4

    assert 3 == my.a
    assert 4 == my["b"]["c"]

    my["a"] = 5
    assert 5 == my.a

    d = my.setdefault("d", dict(e=True))
    assert d.e is True


def test_pickle_dotdict():
    from pickle import dumps as pickle
    from pickle import loads as unpickle

    from temboardtoolkit.utils import DotDict

    orig = DotDict(dict(a=1, b=dict(c=2)))
    copy = unpickle(pickle(orig))
    assert 2 == copy.b.c


def test_ensure_str():
    from temboardtoolkit.taskmanager import ensure_str

    assert type(ensure_str("toto")) is str
    assert type(ensure_str(b"toto")) is str
