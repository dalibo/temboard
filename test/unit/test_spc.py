def  test_set_parameter_status():
    from temboardagent.spc import connector

    c = connector('foo', 'bar', 'dude')
    c._set_parameter_status('server_version', '10.3 (Debian 10.3-1.pgdg90+1)')
    assert c._pg_version == 100300
