from mock import Mock

import pytest


def test_parse_headers_ok():
    from temboardui.autossl import parse_http_headers

    start_line, headers = parse_http_headers(
        "GET / HTTP/1.1\r\n"
        "Host: 0.0.0.0:8888\r\n"
        "\r\n"
        "Pouet\r\n"
    )

    assert 'HTTP/1.1' == start_line.version
    assert 'Host' in headers


def test_parse_headers_nocontents():
    from temboardui.autossl import parse_http_headers

    start_line, headers = parse_http_headers(
        "GET /home HTTP/1.1\r\n"
        "Host: 0.0.0.0:8888\r\n"
    )

    assert 'HTTP/1.1' == start_line.version
    assert 'Host' in headers


def test_switch_response_no_headers():
    from temboardui.autossl import protocol_switcher

    response = protocol_switcher(Mock(
        headers={}, uri='/',
        config=Mock(temboard=dict(address='temboard.lan', port='443'))),
    )

    assert 'https://temboard.lan:443/' == response.headers['Location']


def test_redirect_response_host():
    from temboardui.autossl import protocol_switcher

    response = protocol_switcher(
        Mock(headers={'Host': 'temboard.lan'}, uri='/home'),
    )

    assert 'https://temboard.lan/home' == response.headers['Location']


def test_easy_handshake_ok():
    from tornado import ioloop
    from temboardui.autossl import (
        EasySSLIOStream,
        ssl,
    )

    socket = Mock(name='socket', spec=ssl.SSLSocket)
    io_loop = Mock(name='io_loop', spec=ioloop.IOLoop)
    io_loop.WRITE = ioloop.IOLoop.WRITE
    stream = EasySSLIOStream(socket, io_loop=io_loop)

    stream._do_ssl_handshake()

    assert stream._ssl_accepting is False


def test_easy_handshake_ssl_errors():
    from tornado import ioloop
    from tornado.concurrent import Future
    from temboardui.autossl import (
        EasySSLIOStream,
        ssl,
        SSLErrorHTTPRequest,
    )

    socket = Mock(name='socket', spec=ssl.SSLSocket)
    io_loop = Mock(name='io_loop', spec=ioloop.IOLoop)
    io_loop.WRITE = ioloop.IOLoop.WRITE
    stream = EasySSLIOStream(socket, io_loop=io_loop)

    socket.do_handshake.side_effect = ssl.SSLError(123)
    stream.socket = socket
    with pytest.raises(ssl.SSLError):
        stream._do_ssl_handshake()

    socket.do_handshake.side_effect = ssl.SSLError(ssl.SSL_ERROR_WANT_READ)
    stream.socket = socket
    stream._do_ssl_handshake()
    assert True is stream._handshake_reading

    socket.do_handshake.side_effect = ssl.SSLError(ssl.SSL_ERROR_WANT_WRITE)
    stream.socket = socket
    stream._do_ssl_handshake()
    assert True is stream._handshake_writing

    socket.do_handshake.side_effect = ssl.SSLError(ssl.SSL_ERROR_EOF)
    stream.socket = socket
    stream._do_ssl_handshake()

    socket.do_handshake.side_effect = ssl.SSLError(ssl.SSL_ERROR_SSL)
    socket.getpeername.side_effect = Exception('Unknown test error')
    stream.socket = socket
    stream._do_ssl_handshake()
    assert socket.getpeername.called is True

    socket.do_handshake.side_effect = ssl.SSLError(ssl.SSL_ERROR_SSL)
    socket.getpeername.side_effect = None
    socket.getpeername.reset_mock()
    socket.getpeername.return_value = '127.0.0.1'
    stream.socket = socket
    stream.socket = socket
    stream._do_ssl_handshake()
    assert socket.getpeername.called is True

    socket.do_handshake.side_effect = err = ssl.SSLError(
        ssl.SSL_ERROR_SSL, '[SSL:HTTP_REQUEST] http request',
    )
    # See. https://github.com/python/cpython/blob/8ae264ce/Modules/_ssl.c#L475
    setattr(err, 'reason', 'HTTP_REQUEST')
    socket.getpeername.side_effect = None
    socket.getpeername.reset_mock()
    socket.getpeername.return_value = '127.0.0.1'
    stream.socket = socket
    stream._ssl_connect_future = fut = Future()
    stream._do_ssl_handshake()
    assert socket.getpeername.called is True

    with pytest.raises(SSLErrorHTTPRequest):
        fut.result()


def test_easy_handshake_other_errors():
    from tornado import ioloop
    from temboardui.autossl import (
        EasySSLIOStream,
        errno,
        socket,
        ssl,
    )

    socket_ = Mock(name='socket', spec=ssl.SSLSocket)
    io_loop = Mock(name='io_loop', spec=ioloop.IOLoop)
    io_loop.WRITE = ioloop.IOLoop.WRITE
    stream = EasySSLIOStream(socket_, io_loop=io_loop)

    socket_.do_handshake.side_effect = Exception('Pouet')
    stream.socket = socket
    with pytest.raises(Exception):
        stream._do_ssl_handshake()

    socket_.do_handshake.side_effect = AttributeError('Pouet')
    stream.socket = socket_
    stream._do_ssl_handshake()

    socket_.do_handshake.side_effect = socket.error(errno.EBADF)
    stream.socket = socket_
    stream._do_ssl_handshake()

    socket_.do_handshake.side_effect = socket.error(0)
    stream.socket = socket_
    with pytest.raises(socket.error):
        stream._do_ssl_handshake()


def test_handle_connection(mocker):
    handle_stream = mocker.patch(
        'temboardui.autossl.AutoHTTPSServer.handle_stream'
    )
    ssl_wrap_socket = mocker.patch('temboardui.autossl.ssl_wrap_socket')
    EasySSLIOStream = mocker.patch('temboardui.autossl.EasySSLIOStream')

    from temboardui.autossl import AutoHTTPSServer
    from tornado.concurrent import Future

    server = AutoHTTPSServer(
        request_callback=Mock('request_callback'),
        io_loop=Mock(name='io_loop'),
    )
    server.ssl_options = {'certfile': '/pouet'}
    handle_stream.return_value = Future()
    server._handle_connection(Mock(name='connection'), '127.0.0.1')

    assert ssl_wrap_socket.called is True
    assert EasySSLIOStream.called is True
    assert handle_stream.called is True


@pytest.mark.gen_test
def test_handle_stream_ssl(mocker):
    parent_handle_stream = mocker.patch(
        'temboardui.autossl.HTTPServer.handle_stream'
    )

    from temboardui.autossl import AutoHTTPSServer

    server = AutoHTTPSServer(
        request_callback=Mock('request_callback'),
    )

    ssl_stream = Mock(name='ssl_stream')
    ssl_stream.wait_for_handshake.return_value = []

    yield server.handle_stream(ssl_stream, '127.0.0.1')

    assert ssl_stream.wait_for_handshake.called is True
    assert parent_handle_stream.called is True


@pytest.mark.gen_test
def test_handle_stream_closed(mocker):
    mocker.patch(
        'temboardui.autossl.AutoHTTPSServer.handle_http_connection'
    )
    IOStream = mocker.patch('temboardui.autossl.IOStream')

    from temboardui.autossl import AutoHTTPSServer, StreamClosedError

    server = AutoHTTPSServer(request_callback=Mock('request_callback'))

    ssl_stream = Mock(name='ssl_stream')
    ssl_stream.wait_for_handshake.side_effect = StreamClosedError()

    yield server.handle_stream(ssl_stream, '127.0.0.1')

    assert ssl_stream.wait_for_handshake.called is True
    assert IOStream.called is False


@pytest.mark.gen_test
def test_handle_stream_http_request(mocker):
    parent_handle_stream = mocker.patch(
        'temboardui.autossl.HTTPServer.handle_stream'
    )
    mocker.patch(
        'temboardui.autossl.AutoHTTPSServer.handle_http_connection'
    )
    IOStream = mocker.patch('temboardui.autossl.IOStream')

    from tornado.concurrent import Future
    from temboardui.autossl import AutoHTTPSServer, SSLErrorHTTPRequest

    server = AutoHTTPSServer(request_callback=Mock('request_callback'))

    ssl_stream = Mock(name='ssl_stream')
    ssl_stream.wait_for_handshake.side_effect = SSLErrorHTTPRequest()
    server.handle_http_connection.return_value = fut = Future()
    fut.set_result(None)

    yield server.handle_stream(ssl_stream, '127.0.0.1')

    assert ssl_stream.wait_for_handshake.called is True
    assert IOStream.called is True
    assert server.handle_http_connection.called is True
    assert parent_handle_stream.called is False


@pytest.mark.gen_test
def test_handle_stream_http_request_fails(mocker):
    parent_handle_stream = mocker.patch(
        'temboardui.autossl.HTTPServer.handle_stream'
    )
    mocker.patch(
        'temboardui.autossl.AutoHTTPSServer.handle_http_connection'
    )
    IOStream = mocker.patch('temboardui.autossl.IOStream')

    from temboardui.autossl import AutoHTTPSServer, SSLErrorHTTPRequest

    server = AutoHTTPSServer(request_callback=Mock('request_callback'))

    ssl_stream = Mock(name='ssl_stream')
    ssl_stream.wait_for_handshake.side_effect = SSLErrorHTTPRequest()
    stream = IOStream()
    server.handle_http_connection.side_effect = Exception()

    yield server.handle_stream(ssl_stream, '127.0.0.1')

    assert ssl_stream.wait_for_handshake.called is True
    assert IOStream.called is True
    assert server.handle_http_connection.called is True
    assert parent_handle_stream.called is False
    assert stream.close.called is True


@pytest.mark.gen_test
def test_handle_http_connection_301(mocker):
    HTTPRequest = mocker.patch('temboardui.autossl.HTTPRequest')

    from tornado.concurrent import Future
    from temboardui.autossl import AutoHTTPSServer

    conn = Mock(name='conn')
    conn.stream.read_bytes.return_value = fut = Future()
    fut.set_result(" HTTP/1.1\n")
    conn.write_headers.return_value = fut = Future()
    fut.set_result(None)

    server = AutoHTTPSServer(request_callback=Mock(name='app'))

    yield server.handle_http_connection(conn)

    assert conn.stream.read_bytes.called is True
    assert HTTPRequest.called is True
    assert conn.write_headers.called is True
    _, kw = conn.write_headers.call_args
    assert 301 == kw['start_line'].code
    assert 'Location' in kw['headers']


@pytest.mark.gen_test
def test_handle_http_connection_500(mocker):
    HTTPRequest = mocker.patch('temboardui.autossl.HTTPRequest')

    from tornado.concurrent import Future
    from temboardui.autossl import AutoHTTPSServer

    conn = Mock(name='conn')
    conn.stream.read_bytes.return_value = fut = Future()
    fut.set_result(" HTTP/1.1\n")
    conn.write_headers.return_value = fut = Future()
    fut.set_result(None)

    server = AutoHTTPSServer(request_callback=Mock(name='app'))
    HTTPRequest.side_effect = ValueError()

    yield server.handle_http_connection(conn)

    assert conn.stream.read_bytes.called is True
    assert HTTPRequest.called is True
    assert conn.write_headers.called is True
    _, kw = conn.write_headers.call_args
    assert 500 == kw['start_line'].code
