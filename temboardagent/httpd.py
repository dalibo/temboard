import logging

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urlparse import urlparse, parse_qs
import json
import os
import sys
from urllib import unquote_plus
import signal
import ssl

from temboardagent.routing import get_routes
from temboardagent.errors import HTTPError
from temboardagent import __version__ as temboard_version
from .sharedmemory import Sessions


logger = logging.getLogger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Handle requests in a separate thread. """


class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler.
    """
    def __init__(self, config, sessions, *args, **kwargs):
        """
        Constructor.
        """
        # Sessions array in shared memory.
        self.sessions = sessions
        # Configuration instance.
        self.config = config
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
        logger.info("client: %s request: %s" % (
                         self.address_string(),
                         format % args))

    def response(self):
        """
        In charge to call the main routing function and to return its results
        as a valid HTTP response.
        """
        try:
            (code, message) = self.route_request()
        except HTTPError as e:
            code = e.code
            message = e.message
        except Exception as e:
            # This is an unknown error. Just inform there is an internal error.
            code = 500
            message = {'error': "Internal error."}
            logger.error("Internal error: %s" % (str(e)))
        self.send_response(int(code))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(message).encode('utf-8'))

    def route_request(self,):
        """
        Main function in charge to route the incoming HTTP request to the right
        function.
        """
        # Let's parse and prepare url, path, query etc..
        url_parsed = urlparse(self.path, 'http')
        path = url_parsed.path
        splitpath = path.split('/')
        if len(splitpath) == 1:
            raise HTTPError(404, 'Not found.')
        root = splitpath[1]
        self.query = parse_qs(url_parsed.query)
        # Loop on each defined route in the API.
        for route in get_routes():
            urlvars = []
            is_that_route = True
            # Check that HTTP method and url root are matching.
            if route['http_method'] == self.http_method and \
               route['root'] == root:
                pos = 0
                # Check each element in the path.
                for elt in splitpath[1:]:
                    try:
                        if type(route['splitpath'][pos]) is not str:
                            # Then this is a regular expression.
                            res = route['splitpath'][pos].match(elt)
                            if res is not None:
                                # If the regexp matches, we want to get the
                                #  value and append it in urlvars.
                                urlvars.append(unquote_plus(res.group(1)))
                            else:
                                is_that_route = False
                                break
                        else:
                            if route['splitpath'][pos] != elt:
                                is_that_route = False
                                break
                    except IndexError:
                        is_that_route = False
                        break
                    pos += 1
                if is_that_route:
                    if self.http_method == 'POST':
                        # TODO: raise an HTTP error if the content-length is
                        # too large.
                        try:
                            # Load POST content expecting it is in JSON format.
                            post_raw = self.rfile.read(
                                        int(self.headers['Content-Length']))
                            self.post_json = json.loads(
                                                post_raw.decode('utf-8'))
                        except Exception as e:
                            raise HTTPError(400, 'Invalid json format: %s.'
                                                 % (str(e)))
                    http_context = {
                        'headers': self.headers,
                        'query': self.query,
                        'post': self.post_json,
                        'urlvars': urlvars
                    }
                    # Call the right API function.
                    response = getattr(sys.modules[route['module']],
                                       route['function'])(
                                http_context,
                                self.config,
                                self.sessions)
                    return (200, response)

        raise HTTPError(404, 'URL not found.')


class HTTPDService(object):
    # Manage long running process serving HTTPS API. This include setup, signal
    # management and loop.

    def __init__(self, app):
        self.app = app

    def __enter__(self):
        signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        self.sighup = False

    def __exit__(self, *a):
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    def sighup_handler(self, *a):
        self.sighup = True

    def sigterm_handler(self, *a):
        os._exit(1)

    def run(self):
        self.setup()
        self.serve()

    def serve(self):
        with self:
            while True:
                if self.sighup:
                    self.sighup = False
                    self.reload()
                self.serve1()

    def reload(self):
        self.app.reload()

    def setup(self):
        self.sessions = Sessions(size=100)
        self.httpd = ThreadedHTTPServer(
            (self.app.config.temboard.address, self.app.config.temboard.port),
            self.handle_request)
        self.httpd.socket = ssl.wrap_socket(
            self.httpd.socket,
            keyfile=self.app.config.temboard.ssl_key_file,
            certfile=self.app.config.temboard.ssl_cert_file,
            server_side=True,
        )
        self.httpd.timeout = 1

    def serve1(self):
        self.httpd.handle_request()
        self.sessions.purge_expired(3600, logger, self.app.config)

    def handle_request(self, *args):
        return RequestHandler(self.app.config, self.sessions, *args)
