from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture(scope='session')
def executor():
    yield ThreadPoolExecutor(2)


def test_app_configure(mocker):
    from temboardui.web import WebApplication

    app = WebApplication()
    app.configure(debug=True)
    assert app.settings['autoreload'] is True


def test_app_route(mocker):
    from temboardui.web import WebApplication

    app = WebApplication()

    @app.route('/', methods=['GET', 'POST'])
    def index(request):
        pass

    request = mocker.Mock(name='request', host_name='0.0.0.0', path='/')
    handler = app.default_router.find_handler(request)

    assert handler.handler_kwargs['methods'] == ['GET', 'POST']


def test_handler(executor, io_loop, mocker):
    from temboardui.web import CallableHandler

    mod = 'temboardui.web'
    grbc = mocker.patch(mod + '.get_role_by_cookie')
    mocker.patch(mod + '.DBSession')
    cls = mod + '.CallableHandler'
    gsc = mocker.patch(cls + '.get_secure_cookie')

    callable_ = mocker.MagicMock(__name__='callable', return_value=None)
    handler = CallableHandler(
        mocker.Mock(name='app', ui_methods={}, executor=executor),
        mocker.Mock(name='request'),
        callable_=callable_,
    )
    # Mock handler._execute
    handler._transforms = {}

    io_loop.run_sync(handler.prepare)
    assert handler.request.db_session
    io_loop.run_sync(handler.get)
    assert callable_.called is True

    # Test other get_current_user cases
    grbc.return_value = 'user'
    assert handler.get_current_user() is 'user'

    grbc.side_effect = Exception()
    assert handler.get_current_user() is None

    gsc.return_value = None
    assert handler.get_current_user() is None


def test_redirect(mocker):
    mod = 'temboardui.web'
    cls = mod + '.CallableHandler'
    ssc = mocker.patch(cls + '.set_secure_cookie')
    finish = mocker.patch(cls + '.finish')

    from temboardui.web import CallableHandler, Redirect

    handler = CallableHandler(
        mocker.Mock(name='app', ui_methods={}, executor=executor),
        mocker.Mock(name='request'),
        callable_=mocker.MagicMock(__name__='callable_'),
    )
    # Mock handler._execute
    handler._transforms = {}
    handler.request = mocker.Mock(name='request', uri='/request')

    handler.write_response(Redirect('/redirect'))
    assert ssc.called is True
    assert finish.called is True


def test_template(mocker):
    loader = mocker.patch('temboardui.web.render_template.loader')

    from temboardui.web import render_template

    response = render_template('test.html', var='toto')
    assert loader.load.called is True
    assert 200 == response.status_code
