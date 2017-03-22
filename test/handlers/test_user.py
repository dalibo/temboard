from mock import Mock


def test_json_login(mocker):
    mocker.patch('temboardui.handlers.user.sleep')
    mocker.patch('temboardui.handlers.user.get_role_by_auth')

    from tornado.escape import json_encode
    from temboardui.handlers.user import LoginJsonHandler

    handler = LoginJsonHandler(
        application=Mock(name='app', ui_methods={}),
        request=Mock(name='request'),
        template_path='WTF',
        ssl_ca_cert_file='WTF',
    )
    handler.db_session = Mock(name='db_session')

    handler.request.body = json_encode({
        'username': 'toto',
        'password': 'toto',
    })

    response = handler.post_login()

    assert 200 == response.http_code
    assert response.secure_cookie
