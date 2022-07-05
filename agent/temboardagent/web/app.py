import functools
import inspect
import logging
import json
from datetime import datetime, timedelta, timezone

from bottle import (
    Bottle,
    HTTPError, HTTPResponse, Response,
    default_app, request, response,
)
from psycopg2 import Error as Psycopg2Error

from ..tools import JSONEncoder
from ..toolkit.http import format_date
from ..toolkit.signing import (
    InvalidSignature,
    canonicalize_request,
    verify_v1,
)


logger = logging.getLogger(__name__)


def create_app(temboard):
    Response.default_content_type = 'text/plain'
    app = CustomBottle(autojson=False)
    app.temboard = temboard
    app.add_hook('before_request', before_request_log)
    app.add_hook('after_request', after_request_log)
    app.install(JSONPlugin())
    app.install(ErrorPlugin())
    app.install(SignaturePlugin())
    app.install(PostgresPlugin())
    return app


class CustomBottle(Bottle):
    def default_error_handler(self, res):
        # Skip HTML template.
        return res.body

    def __call__(self, environ, start_response):
        # Keep a copy of the original PATH_INFO, before bottle modifies it.
        environ['ORIG_PATH_INFO'] = environ['PATH_INFO']
        return super(CustomBottle, self).__call__(environ, start_response)

    def mount(self, prefix, app, **options):
        for plugin in self.plugins:
            app.install(plugin)
        return super(CustomBottle, self).mount(prefix, app, **options)


def before_request_log():
    logger.debug("New web request: %s %s", request.method, request.path)


def after_request_log():
    if response.status_code > 500:
        logmethod = logger.error
    else:
        logmethod = logger.info
    logmethod("%s %s %s", request.method, request.path, response.status)


class PostgresPlugin(object):
    def __init__(self):
        self._pool = None
        self._dbpool = None

    @property
    def dbpool(self):
        if not self._dbpool:
            self._dbpool = default_app().temboard.postgres.dbpool()
        return self._dbpool

    @property
    def pool(self):
        if not self._pool:
            self._pool = default_app().temboard.postgres.pool()
        return self._pool

    def apply(self, callback, route):
        wanted = self.wants_postgres(callback)
        if not wanted:
            return callback

        @functools.wraps(callback)
        def wrapper(*a, **kw):
            # Retry execution one time to handle closed connection. This assume
            # callbacks idempotence.
            for try_ in 0, 1:
                if 'pgconn' in wanted:
                    conn = self.pool.getconn()
                    conn.set_session(autocommit=True)
                    kw['pgconn'] = conn

                if 'pgpool' in wanted:
                    # dbpool is not threadsafe! But wsgiref simple server is
                    # not threaded.
                    kw['pgpool'] = self.dbpool

                try:
                    return callback(*a, **kw)
                except Psycopg2Error as e:
                    if e.pgcode is None:
                        logger.debug("Retrying lost connection: %s", e)
                        self.dbpool.closeall()
                        self.pool.closeall()
                finally:
                    if 'pgconn' in wanted:
                        self.pool.putconn(conn)

        return wrapper

    def wants_postgres(self, callback):
        argspec = inspect.getargspec(callback)
        return [a for a in argspec.args if a in ('pgconn', 'pgpool')]


class ErrorPlugin(object):
    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*a, **kw):
            try:
                response = callback(*a, **kw)
            except HTTPError as e:
                if isinstance(e.body, str):
                    e.body = {'error': e.body}
                logger.debug("Error: %s.", e.body)
                raise
            except HTTPResponse:
                raise
            except Exception:
                logger.exception("Unhandled error:")
                response = HTTPResponse({'error': 'Internal error.'}, 500)

            return response
        return wrapper


class JSONPlugin(object):
    # Bottle jsonify only dict. JSON Array was a security issue for some
    # browser.
    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*a, **kw):
            res = callback(*a, **kw)
            body = res.body if isinstance(res, HTTPResponse) else res

            if not isinstance(body, (dict, list)):
                return res

            body = json.dumps(body, cls=JSONEncoder)
            if isinstance(res, HTTPResponse):
                res.body = body
            else:
                res = HTTPResponse(body)

            res.headers['Content-Type'] = 'application/json'

            return res
        return wrapper


class SignaturePlugin(object):
    name = 'signature'

    def setup(self, app):
        self.app = app

    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*a, **kw):
            request.username = self.authenticate()
            return callback(*a, **kw)
        return wrapper

    def authenticate(self):
        app = default_app().temboard

        date = request.headers['x-temboard-date']
        utcnow = datetime.utcnow().replace(tzinfo=timezone.utc)
        oldest_date = format_date(utcnow - timedelta(hours=2))
        if date < oldest_date:
            raise HTTPError(400, "Request older than 2 hours.")

        signature = request.headers['x-temboard-signature']
        version, _, signature = signature.partition(':')
        if 'v1' != version:
            raise HTTPError(400, 'Unsupported signature format')

        if not signature:
            raise HTTPError(400, 'Malformed signature')

        path = request.environ['ORIG_PATH_INFO']
        if request.environ['QUERY_STRING']:
            path = path + '?' + request.environ['QUERY_STRING']
        canonical_request = canonicalize_request(
            request.method, path, request.headers, request.body.read(),
        )

        try:
            verify_v1(app.config.signing_key, signature, canonical_request)
        except InvalidSignature:
            raise HTTPError(403, 'Invalid signature')

        user = request.headers.get('x-temboard-user')
        if not user:
            raise HTTPError(400, 'Missing username')

        return user
