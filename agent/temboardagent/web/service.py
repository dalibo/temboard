import logging
import json
import ssl
import sys
from socket import error as SocketError
from urllib.parse import urlparse, parse_qs, unquote_plus
from wsgiref.simple_server import make_server

from bottle import debug, default_app, HTTPResponse, request

from .. import __version__ as temboard_version
from .. import errors
from ..errors import UserError
from ..routing import get_routes
from ..toolkit.services import Service
from ..tools import JSONEncoder


logger = logging.getLogger(__name__)


class HTTPDService(Service):
    def setup(self):
        try:
            bottle = default_app()
            debug(self.app.debug)
            # Register legacy fallback **last**.
            bottle.route(
                '<path:re:/.+>', callback=legacy_fallback,
                method='ANY',
            )

            self.server = make_server(
                self.app.config.temboard.address,
                self.app.config.temboard.port,
                app=bottle,
            )
        except SocketError as e:
            raise UserError("Failed to start HTTPS server: {}.".format(e))
        try:
            logger.debug(
                "Using SSL key %s.", self.app.config.temboard.ssl_key_file)
            logger.debug(
                "Using SSL certificate %s.",
                self.app.config.temboard.ssl_cert_file)
            self.server.socket = ssl.wrap_socket(
                self.server.socket,
                keyfile=self.app.config.temboard.ssl_key_file,
                certfile=self.app.config.temboard.ssl_cert_file,
                server_side=True,
            )
        except Exception as e:
            raise UserError("Failed to setup SSL: {}.".format(e))
        self.server.timeout = 1

    def serve1(self):
        self.server.handle_request()


def legacy_fallback(path):
    if request.query_string:
        path = path + '?' + request.query_string

    handler = RequestHandler(
        app=default_app().temboard,
        method=request.method,
        path=path,
        headers=request.headers,
        body=request.body.read(),
        username=request.username,
    )

    try:
        code, body = handler.route_request()
    except errors.HTTPError as e:
        code = e.code
        body = {'error', str(e)}
    except Exception:
        logger.exception("Unhandled error:")
        code = 500
        body = {'error': 'Internal error.'}

    if isinstance(body, list):
        # Bottle does not serialiaze list. There was security issue in browser.
        body = json.dumps(body, cls=JSONEncoder)

    return HTTPResponse(
        body=body,
        status=code,
    )


class RequestHandler(object):
    """
    HTTP request handler.
    """
    def __init__(self, app, method, path, headers, body, username):
        """
        Constructor.
        """
        # Application instance.
        self.app = app
        # HTTP server version.
        self.server_version = "temboard-agent/%s" % temboard_version
        # HTTP request method
        self.http_method = method

        self.path = path
        self.headers = headers
        self.body = body
        self.username = username

    def get_route(self, method, path):
        # Returns the right route according to method/path
        s_path = path.split(b'/')[1:]
        root = s_path[0]
        for route in get_routes():
            # Check that HTTP method and url root are matching.
            if not (route['http_method'] == self.http_method and
                    route['root'] == root):
                continue

            p = 0
            # Check each element in the path.
            for elt in s_path:
                try:
                    if type(route['splitpath'][p]) not in (str, bytes):
                        # Then this is a regular expression.
                        res = route['splitpath'][p].match(elt.decode('utf-8'))
                        if not res:
                            break
                    else:
                        if route['splitpath'][p] != elt:
                            break
                except IndexError:
                    break
                p += 1
            if p == len(s_path) == len(route['splitpath']):
                return route
        raise errors.HTTPError(404, 'URL not found.')

    def parse_path(self, path, route):
        # Parse an URL path when route's path contains regepx
        p = 0
        urlvars = list()
        for elt in path.split(b'/')[1:]:
            if type(route['splitpath'][p]) not in (str, bytes):
                # Then this is a regular expression.
                res = route['splitpath'][p].match(elt.decode('utf-8'))
                if res is not None:
                    # If the regexp matches, we want to get the
                    # value and append it in urlvars.
                    urlvars.append(unquote_plus(res.group(1)))
            p += 1
        return urlvars

    def route_request(self,):
        """
        Main function in charge to route the incoming HTTP request to the right
        function.
        """
        # Let's parse and prepare url, path, query etc..
        up = urlparse(self.path, 'http')
        splitpath = up.path.split('/')
        if len(splitpath) == 1:
            raise errors.HTTPError(404, 'Not found.')
        query = parse_qs(up.query)

        # Get the route
        route = self.get_route(self.http_method, up.path.encode('utf-8'))
        # Parse URL path
        urlvars = self.parse_path(up.path.encode('utf-8'), route)

        post_json = None
        try:
            # Load POST content expecting it is in JSON format.
            if self.http_method == 'POST':
                post_json = json.loads(self.body.decode('utf-8'))
        except Exception as e:
            logger.exception(str(e))
            logger.error('Invalid json format')
            raise errors.HTTPError(400, 'Invalid json format')

        http_context = dict(
            app=self.app,
            method=self.http_method,
            headers=self.headers,
            path=up.path,
            query=query,
            post=post_json,
            urlvars=urlvars,
            username=self.username,
        )

        # Handle the request
        func = getattr(sys.modules[route['module']], route['function'])
        return 200, func(http_context, self.app)
