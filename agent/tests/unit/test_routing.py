def test_make_route():
    from temboardagent.routing import make_route

    def f():
        pass

    path = b'/foo'
    r = make_route(f, 'm', path, True, True)
    assert r['function'] == 'f'
    assert r['path'] == path
    assert r['splitpath'][0] == b'foo'

    path = b'/foo/bar'
    r = make_route(f, 'm', path, True, True)
    assert len(r['splitpath']) == 2

    T_SOMETHING = b'(^[a-z]{1,100}$)'
    path = b'/foo/' + T_SOMETHING
    r = make_route(f, 'm', path, True, True)
    assert len(r['splitpath']) == 2

    T_BAR = b'(bar)'
    T_DUDE = b'(^.{1,128}$)'
    path = b'/foo/' + T_BAR + b'/' + T_DUDE
    r = make_route(f, 'm', path, True, True)
    assert len(r['splitpath']) == 3

    # # check path part is a compiled regexp
    assert hasattr(r['splitpath'][1], 'match')
    assert r['splitpath'][1].match('bar')
    assert not r['splitpath'][1].match('dude')
    assert r['splitpath'][2].match('4nyth1ng')
