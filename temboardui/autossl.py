# -*- coding: utf-8 -*-
#
# This module implements protocol switching from HTTP to HTTPS on the same
# socket connection.
#
# In tornado, a bunch of objects interacts with each other to handle a request:
# IOStream, TCP/HTTPServer, HTTP1Connection, HTTPMessageDelegate, HTTPRequest,
# HTTPResponse and HTTPRequestHandler. But it's not as simple as an onion of
# successive encapsulations.
#
# OpenSSL raises an error on uncrypted HTTP request while waiting for
# handshake. The first step is to have an IOStream with explicit SSL handshake
# allowing to catch this OpenSSL error. This stream must NOT close the socket
# on error.
#
# On HTTP request, we divert the request processing to the protocol switcher.
# The protocol switcher almost look like a regular request/response handling
# but there is no routing. We limit processing to headers to preserver host and
# path of the request.
#
# All of this (handshake, read request and write response) must be async to
# keep the server loop managing all incoming connections.

import errno
import logging
import socket
import ssl

from tornado import gen
from tornado.httpserver import HTTPServer, HTTPRequest
from tornado.httpclient import HTTPResponse
from tornado.httputil import (
    HTTPHeaders,
    parse_request_start_line,
    ResponseStartLine,
)
from tornado.http1connection import HTTP1Connection
from tornado.ioloop import IOLoop
from tornado.iostream import (
    IOStream,
    SSLIOStream,
    StreamClosedError,
)
from tornado.log import (
    app_log,
    gen_log,
)
from tornado.netutil import ssl_wrap_socket
from tornado.util import errno_from_exception


logger = logging.getLogger(__name__)


def parse_http_headers(payload):
    # Implements simple HTTP1Connection._read_message but IO-free.
    lines = payload.splitlines()
    if lines and ':' not in lines[0]:
        # Drop start line
        lines.pop(0)
    # Drop contents
    if '' in lines:
        lines[:] = lines[:lines.index('')]
    return (
        parse_request_start_line('GET / HTTP/1.1'),
        HTTPHeaders.parse('\r\n'.join(lines)),
    )


def protocol_switcher(request):
    try:
        host = request.headers['Host']
    except KeyError:
        # We don't have FQDN. Fallback to socket address. This breaks
        # name-based virtualhost.
        host = '%(address)s:%(port)s' % dict(
            request.config.temboard, address=request.host)
    new_url = 'https://%s%s' % (host, request.uri)
    headers = HTTPHeaders({
        'Content-Length': '0',
        'Location': new_url,
    })
    logger.debug("Redirecting client to %s.", new_url)
    return HTTPResponse(
        request=request, code=301, headers=headers,
        # If effective_url is not set, HTTPResponse falls back to request.url,
        # which does not exists... See tornado.httpclient.HTTPResponse.__init__
        # and tornado.httpserver.HTTPRequest.
        effective_url=request.full_url(),
    )


class SSLErrorHTTPRequest(Exception):
    pass


class EasySSLIOStream(SSLIOStream):
    # SSIOStream raising exception on HTTP_REQUEST rather than closing socket.

    def _do_ssl_handshake(self):
        # Based on code from test_ssl.py in the python stdlib
        try:
            self._handshake_reading = False
            self._handshake_writing = False
            self.socket.do_handshake()
        except ssl.SSLError as err:
            if err.args[0] == ssl.SSL_ERROR_WANT_READ:
                self._handshake_reading = True
                return
            elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                self._handshake_writing = True
                return
            elif err.args[0] in (ssl.SSL_ERROR_EOF,
                                 ssl.SSL_ERROR_ZERO_RETURN):
                return self.close(exc_info=True)
            elif err.args[0] == ssl.SSL_ERROR_SSL:
                try:
                    peer = self.socket.getpeername()
                except Exception:
                    peer = '(not connected)'

                if getattr(err, 'reason', None) == 'HTTP_REQUEST':
                    # Async raise HTTP_REQUEST error.
                    self._ssl_connect_future.set_exception(
                        SSLErrorHTTPRequest()
                    )
                    gen_log.warning("HTTP_REQUESTS on SSL handshake from %s.",
                                    peer)
                    return

                gen_log.warning("SSL Error on %s %s: %s",
                                self.socket.fileno(), peer, err)
                return self.close(exc_info=True)
            raise
        except socket.error as err:
            # Some port scans (e.g. nmap in -sT mode) have been known
            # to cause do_handshake to raise EBADF and ENOTCONN, so make
            # those errors quiet as well.
            # https://groups.google.com/forum/?fromgroups#!topic/python-tornado/ApucKJat1_0
            if (self._is_connreset(err) or
                    err.args[0] in (errno.EBADF, errno.ENOTCONN)):
                return self.close(exc_info=True)
            raise
        except AttributeError:
            # On Linux, if the connection was reset before the call to
            # wrap_socket, do_handshake will fail with an
            # AttributeError.
            return self.close(exc_info=True)
        else:
            self._ssl_accepting = False
            if not self._verify_cert(self.socket.getpeercert()):
                self.close()
                return
            self._run_ssl_connect_callback()


class AutoHTTPSServer(HTTPServer):
    # HTTPServer implementing protocol switching.

    def _handle_connection(self, connection, address):
        # Copy-paste of tornado.httpserver.HTTPServer._handle_connection to use
        # our custom stream class.
        #
        # Actually, connection is just a socket.
        try:
            connection = ssl_wrap_socket(connection,
                                         self.ssl_options,
                                         server_side=True,
                                         do_handshake_on_connect=False)
        except ssl.SSLError as err:
            if err.args[0] == ssl.SSL_ERROR_EOF:
                return connection.close()
            else:
                raise
        except socket.error as err:
            # If the connection is closed immediately after it is created
            # (as in a port scan), we can get one of several errors.
            # wrap_socket makes an internal call to getpeername,
            # which may return either EINVAL (Mac OS X) or ENOTCONN
            # (Linux).  If it returns ENOTCONN, this error is
            # silently swallowed by the ssl module, so we need to
            # catch another error later on (AttributeError in
            # SSLIOStream._do_ssl_handshake).
            # To test this behavior, try nmap with the -sT flag.
            # https://github.com/tornadoweb/tornado/pull/750
            if errno_from_exception(err) in (errno.ECONNABORTED, errno.EINVAL):  # noqa
                return connection.close()
            else:
                raise
        try:
            io_loop = self.io_loop
            kw = dict(io_loop=io_loop)
        except AttributeError:
            # We are on Tornado 5+. Just don't pass ioloop
            kw = {}
            io_loop = IOLoop.current()

        try:
            stream = EasySSLIOStream(
                connection,
                max_buffer_size=self.max_buffer_size,
                read_chunk_size=self.read_chunk_size,
                **kw
            )
            future = self.handle_stream(stream, address)
            if future is not None:
                io_loop.add_future(future, lambda f: f.result())
        except Exception:
            app_log.error("Error in connection callback", exc_info=True)

    @gen.coroutine
    def handle_stream(self, ssl_stream, address):
        try:
            yield ssl_stream.wait_for_handshake()
        except SSLErrorHTTPRequest:
            stream = IOStream(ssl_stream.socket._sock)
            conn = HTTP1Connection(stream, is_client=False)
            try:
                yield self.handle_http_connection(conn)
            except Exception:
                logger.exception("Failed to process HTTP request:")
            finally:
                stream.close()
        except StreamClosedError:
            logger.debug("Stream closed by client during handshake. Skipping.")
            return
        else:
            super(AutoHTTPSServer, self).handle_stream(ssl_stream, address)

    @gen.coroutine
    def handle_http_connection(self, conn):
        # Read the trailing HTTP request and process it with protocol_switcher.
        # We can't rely on ioloop to trigger read because it has been already
        # triggered for SSL handshake.
        addr, port = conn.stream.socket.getsockname()
        try:
            # This is not blocking. Just read available bytes.
            payload = conn.stream.socket.recv(1024)
        except Exception:
            # Exception includes EWOULDBLOCK, when no bytes are available. In
            # this case just skip.
            payload = ""
        else:
            logger.debug("Received %r", payload[:128])
        # Simulate conn._read_message side effect. This is required by
        # HTTP1Connection.write_headers()
        conn._request_start_line = parse_request_start_line('GET / HTTP/1.1')
        try:
            start_line, headers = parse_http_headers(payload)
            conn._request_start_line = start_line
            request = HTTPRequest(
                connection=conn,
                headers=headers,
                start_line=start_line,
            )
            request.config = self.request_callback.config
            response = protocol_switcher(request)
        except Exception as e:
            logger.error("Failed to switch to HTTPS: %s", e)
            response = HTTPResponse(
                request=object(), code=500,
                headers=HTTPHeaders({'Content-Length': '0'}),
                effective_url='https://useless_effective_url'
            )
        yield conn.write_headers(
            start_line=ResponseStartLine(
                'HTTP/1.1', response.code, response.reason,
            ),
            headers=response.headers,
        )
