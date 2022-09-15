import functools
import inspect
import logging
import json
from datetime import timedelta

from bottle import (
    Bottle,
    HTTPError, HTTPResponse, Response,
    default_app, request, response,
)

from ..toolkit.utils import JSONEncoder, utcnow
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
    # First declared, first executed.
    app.install(JSONPlugin())
    app.install(ErrorPlugin())
    app.install(SignaturePlugin())
    app.install(PostgresPlugin())
    return app


class CustomBottle(Bottle):
    def default_error_handler(self, res):
        # Skip HTML template.
        return res.body

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
            if 'pgpool' in wanted:
                # dbpool is not threadsafe! But wsgiref simple server is
                # not threaded.
                kw['pgpool'] = self.dbpool

            # Assume callbacks idempotence.
            for attempt in self.pool.retry_connection():
                with attempt() as conn:
                    if 'pgconn' in wanted:
                        kw['pgconn'] = conn

                    return callback(*a, **kw)

                if attempt.retry:
                    # Propagate connection lost to dbpool.
                    self.dbpool.closeall()

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
                # Use HTTPResponse to customize body.
                response = HTTPResponse(e.body, e.status)
            except HTTPResponse as e:
                response = e
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
            if not isinstance(res, HTTPResponse):
                res = response.copy(cls=HTTPResponse)
            res.body = body

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
        oldest_date = format_date(utcnow() - timedelta(hours=2))
        if date < oldest_date:
            raise HTTPError(400, "Request older than 2 hours.")

        signature = request.headers['x-temboard-signature']
        version, _, signature = signature.partition(':')
        if 'v1' != version:
            raise HTTPError(400, 'Unsupported signature format')

        if not signature:
            raise HTTPError(400, 'Malformed signature')

        path = request.environ['RAW_PATH_INFO']
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
