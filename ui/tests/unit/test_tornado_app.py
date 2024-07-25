from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture(scope="session")
def executor():
    yield ThreadPoolExecutor(2)


def test_app_configure(mocker):
    from temboardui.web.tornado import WebApplication

    app = WebApplication()
    app.configure(debug=True)
    assert app.settings["autoreload"] is True


def test_app_route(mocker):
    from temboardui.web.tornado import WebApplication

    app = WebApplication()

    @app.route("/", methods=["GET", "POST"])
    def index(request):
        yield ""

    request = mocker.Mock(name="request", host_name="0.0.0.0", path="/")
    router = app.default_router
    handler = router.find_handler(request)
    kwargs = handler.handler_kwargs

    assert kwargs["methods"] == ["GET", "POST"]


def test_handler(executor, io_loop, mocker):
    from temboardui.web.tornado import CallableHandler
    from tornado.gen import coroutine

    mod = "temboardui.web.tornado"
    grbc = mocker.patch(mod + ".get_role_by_cookie")
    mocker.patch(mod + ".DBSession")
    cls = mod + ".CallableHandler"
    gsc = mocker.patch(cls + ".get_secure_cookie")

    @coroutine
    def callable_(*a):
        return

    handler = CallableHandler(
        mocker.Mock(name="app", ui_methods={}, executor=executor),
        mocker.Mock(name="request"),
        callable_=mocker.Mock(side_effect=callable_),
    )
    # Mock handler._execute
    handler._transforms = {}
    handler.db_session = mocker.Mock()

    io_loop.run_sync(handler.prepare)
    assert handler.request.db_session
    io_loop.run_sync(handler.get)
    assert handler.callable_.called is True

    # Test other get_current_user cases
    grbc.return_value = "user"
    assert handler.get_current_user() == "user"

    grbc.side_effect = Exception()
    assert handler.get_current_user() is None

    gsc.return_value = None
    assert handler.get_current_user() is None


def test_template(mocker):
    loader = mocker.patch("temboardui.web.tornado.render_template.loader")

    from temboardui.web.tornado import render_template

    response = render_template("test.html", var="toto")
    assert loader.load.called is True
    assert 200 == response.status_code


def test_csv():
    from temboardui.web.tornado import csvify

    response = csvify("1,2")
    assert "1,2" == response.body
    assert "text/csv" == response.headers["Content-Type"]

    response = csvify([(1, 2)])
    assert "1,2" in response.body.splitlines()
    assert "text/csv" == response.headers["Content-Type"]

    with pytest.raises(ValueError):
        csvify({"a": "b"})


def test_make_error(mocker):
    rt = mocker.patch("temboardui.web.tornado.render_template")
    from temboardui.web.tornado import make_error
    from tornado.httputil import HTTPServerRequest

    response_kw = dict(
        name="request",
        current_user=None,
        handler=mocker.Mock(name="handler"),
        spec=HTTPServerRequest,
    )

    # Errors are rendered with HTML template
    response = make_error(
        mocker.Mock(path="/home", **response_kw), code=401, message=None
    )
    assert rt.called is True
    assert 401 == response.status_code

    # /json request has json errors
    response = make_error(
        mocker.Mock(json={"request": True}, **response_kw), code=401, message="Pouet"
    )

    assert "Pouet" == response.body["error"]
    assert 401 == response.status_code

    # ?noerror=1 request always has empty 200 response
    request = mocker.Mock(path="/json/settings/roles", **response_kw)
    request.handler.get_argument.return_value = "1"
    response = make_error(request, code=401, message="Pouet")

    assert not response.body
    assert 200 == response.status_code
