def test_filter_pg_version():
    from temboardui.toolkit.queries import filter_pragma_version

    assert filter_pragma_version("pouet", pg_version=150000)

    sql = "pouet -- pragma:pg_version_max 140000"
    assert not filter_pragma_version(sql, pg_version=150000)
    assert filter_pragma_version(sql, pg_version=100000)

    sql = "pouet -- pragma:pg_version_min 140000"
    assert not filter_pragma_version(sql, pg_version=100000)
    assert filter_pragma_version(sql, pg_version=150000)
