import pytest


def test_csv():
    from temboardui.web.flask import csvify

    response = csvify("1,2")
    assert "1,2" == response.get_data(as_text=True)
    assert "text/csv" == response.headers["Content-Type"]

    response = csvify([(1, 2)])
    assert "1,2" in response.get_data(as_text=True).splitlines()
    assert "text/csv" == response.headers["Content-Type"]

    with pytest.raises(ValueError):
        csvify({"a": "b"})
