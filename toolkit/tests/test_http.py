def test_join_query_empty():
    from temboardtoolkit.http import join_query

    assert "/path" == join_query("/path")
    assert "/path" == join_query("/path", None)
    assert "/path" == join_query("/path", {})
    assert "/path" == join_query("/path", [])


def test_join_query_dict():
    from temboardtoolkit.http import join_query

    assert "/path?a=1&b=two" == join_query("/path", dict(a=1, b="two"))


def test_join_query_pairs():
    from temboardtoolkit.http import join_query

    # Pairs preserve order and allow repeated names.
    assert "/path?b=1&a=2&b=3" == join_query("/path", [("b", 1), ("a", 2), ("b", 3)])


def test_join_query_list_value():
    from temboardtoolkit.http import join_query

    assert "/path?s=1&s=2" == join_query("/path", dict(s=[1, 2]))


def test_join_query_escape():
    from temboardtoolkit.http import join_query

    assert "/path?q=x+y&e=%C3%A9&amp=%26%3D" == join_query(
        "/path", dict(q="x y", e="é", amp="&=")
    )


def test_join_query_existing_query():
    from temboardtoolkit.http import join_query

    assert "/path?a=1&b=2" == join_query("/path?a=1", dict(b=2))
