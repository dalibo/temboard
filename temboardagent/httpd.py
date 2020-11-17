import logging
import time

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import urlparse, parse_qs, unquote_plus
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urlparse import urlparse, parse_qs
    from urllib import unquote_plus
import json
import sys
from socket import error as SocketError
import ssl

from temboardagent.routing import get_routes
from temboardagent.errors import HTTPError
from temboardagent.tools import JSONEncoder
from temboardagent import __version__ as temboard_version
from .sharedmemory import Sessions
from .api import check_sessionid
from .errors import UserError
from .toolkit.services import Service


logger = logging.getLogger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Handle requests in a separate thread. """


class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler.
    """
    def __init__(self, app, sessions, *args, **kwargs):
        """
        Constructor.
        """
        # Sessions array in shared memory.
        self.sessions = sessions
        # Application instance.
        self.app = app
        # HTTP server version.
        self.server_version = "temboard-agent/%s" % temboard_version
        # HTTP request method
        self.http_method = None
        # HTTP query.
        self.query = None
        # HTTP POST content in json format.
        self.post_json = None
        # Call HTTP request handler constructor.
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_GET(self):
        """
        Handle HTTP GET requests.
        """
        self.http_method = 'GET'
        self.response()

    def do_POST(self,):
        """
        Handle HTTP POST requests.
        """
        self.http_method = 'POST'
        self.response()

    def do_PUT(self,):
        """
        Handle HTTP PUT requests.
        """
        self.http_method = 'PUT'
        # Nothing to do for now.
        pass

    def do_DELETE(self,):
        """
        Handle HTTP DELETE requests.
        """
        self.http_method = 'DELETE'
        self.response()

    def do_OPTIONS(self,):
        self.send_response(200, "OK")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods',
                         'POST, GET, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         "X-Requested-With, X-Session, Content-Type")
        self.send_header('Access-Control-Max-Age', '1728000')
        self.end_headers()
        logger.info(self.headers.dict['origin'])

    def log_message(self, format, *args):
        """
        Overrides log_message() for HTTP requests logging with our own logger.
        """
        logger.info("client: %s request: %s"
                    % (self.address_string(), format % args))

    def handle_one_request(self, *a, **kw):
        self.start_time = time.time()
        return BaseHTTPRequestHandler.handle_one_request(self, *a, **kw)

    def request_time(self):
        return 1000. * (time.time() - self.start_time)

    def log_request(self, code='-', size='-'):
        """Log an accepted request.

        This is called by send_response().

        """
        if hasattr(code, 'value'):
            code = code.value
        self.log_message(
            '"%s" %s %s %.2fms',
            self.requestline, str(code), str(size), self.request_time(),
        )

    def response(self):
        """
        In charge to call the main routing function and to return its results
        as a valid HTTP response.
        """
        try:
            (code, message) = self.route_request()
        except HTTPError as e:
            logger.exception(e.message)
            logger.error(e.message)
            code = e.code
            message = e.message
        except UserError as e:
            msg = str(e)
            logger.exception(msg)
            logger.error(msg)
            code = 500
            message = {'error': msg}
        except Exception as e:
            logger.exception(str(e))
            logger.error("Internal error")
            # This is an unknown error. Just inform there is an internal error.
            code = 500
            message = {'error': "Internal error."}

        try:
            # Try to send the response
            self.send_response(int(code))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(message, cls=JSONEncoder)
                             .encode('utf-8'))
        except Exception as e:
            logger.exception(str(e))
            logger.error("Could not send response")

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
                logger.debug(route)
                return route
        raise HTTPError(404, 'URL not found.')

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
        path = up.path
        splitpath = path.split('/')
        if len(splitpath) == 1:
            raise HTTPError(404, 'Not found.')
        self.query = parse_qs(up.query)

        # Get the route
        route = self.get_route(self.http_method, path.encode('utf-8'))
        # Parse URL path
        urlvars = self.parse_path(path.encode('utf-8'), route)
        post_raw = None
        # Load POST content if any
        if self.http_method == 'POST':
            # TODO: raise an HTTP error if the content-length is
            # too large.
            try:
                post_raw = self.rfile.read(int(self.headers['Content-Length']))
            except Exception as e:
                logger.exception(str(e))
                logger.debug(self.headers)
                logger.error('Unable to read post data')
                raise HTTPError(400, 'Unable to read post data')

        username = None
        checked = False

        # Authentication checking out

        # 1. Try the auth' by key: if this method is available for this API
        # and 'key' arg exists.
        if route['check_key'] and 'key' in self.query:
            if self.app.config.temboard.key is None:
                raise HTTPError(401, "Authentication key not configured")
            if self.query['key'][0] != self.app.config.temboard.key:
                raise HTTPError(401, "Invalid key")
            checked = True

        # 2. Check session ID if available and not previously auth'd by key
        if not checked and route['check_session']:
            username = check_sessionid(self.headers, self.sessions)
            checked = True

        # 3. At this point, if not yet checked out and auth' by key is
        # available then we need to raise an error because 'key' arg hasn't
        # been passed and auth' by key is the only available method.
        if not checked and route['check_key']:
            raise HTTPError(401, "Missing key")

        try:
            # Load POST content expecting it is in JSON format.
            if self.http_method == 'POST':
                self.post_json = json.loads(post_raw.decode('utf-8'))
        except Exception as e:
            logger.exception(str(e))
            logger.error('Invalid json format')
            raise HTTPError(400, 'Invalid json format')

        http_context = dict(
            headers=self.headers,
            query=self.query,
            post=self.post_json,
            urlvars=urlvars,
            username=username,
        )

        # Handle the request
        func = getattr(sys.modules[route['module']], route['function'])
        if route['module'] == 'temboardagent.api':
            # some core APIs need to deal with sessions
            return (200, func(http_context, self.app, self.sessions))
        else:
            # plugin
            return (200, func(http_context, self.app))


class HTTPDService(Service):
    def setup(self):
        self.sessions = Sessions(size=100)
        try:
            self.httpd = ThreadedHTTPServer(
                (self.app.config.temboard.address,
                 self.app.config.temboard.port),
                self.handle_request)
        except SocketError as e:
            raise UserError("Failed to start HTTPS server: %s." % (e,))
        try:
            logger.debug(
                "Using SSL key %s.", self.app.config.temboard.ssl_key_file)
            logger.debug(
                "Using SSL certificate %s.",
                self.app.config.temboard.ssl_cert_file)
            self.httpd.socket = ssl.wrap_socket(
                self.httpd.socket,
                keyfile=self.app.config.temboard.ssl_key_file,
                certfile=self.app.config.temboard.ssl_cert_file,
                server_side=True,
            )
        except Exception as e:
            raise UserError("Failed to setup SSL: %s." % (e,))
        self.httpd.timeout = 1

    def serve1(self):
        self.httpd.handle_request()
        self.sessions.purge_expired(3600, logger, self.app.config)

    def handle_request(self, *args):
        return RequestHandler(self.app, self.sessions, *args)
