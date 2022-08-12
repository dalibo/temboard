import logging
from ipaddress import ip_address, ip_network

from flask import Flask, abort, g, request, jsonify
from werkzeug.exceptions import HTTPException
from tornado.web import decode_signed_value

from ..application import (
    get_role_by_cookie,
)
from ..model import Session
from ..model.orm import ApiKeys, StubRole


logger = logging.getLogger(__name__)


def create_app(temboard_app):
    app = Flask('temboardui', static_folder=None)
    app.temboard = temboard_app
    SQLAlchemy(app)
    APIKeyMiddleware(app)
    UserMiddleware(app)
    AuthMiddleware(app)
    app.errorhandler(Exception)(json_error_handler)
    return app


def json_error_handler(e):
    if isinstance(e, HTTPException):
        if e.code < 500:
            logger.warning("User error: %s", e)
        else:
            logger.error("Fatal error: %s", e)
    else:
        logger.exception("Unhandled error:")
    return jsonify(error=str(e) or repr(e))


class SQLAlchemy(object):
    # Flask extension to manage a SQLAlchemy session per request.
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.db = self
        app.before_request(self.before)
        app.teardown_request(self.teardown)

    def before(self):
        g.db_session = Session()

    def teardown(self, error):
        if error:
            # Expunge objects before rollback to implement
            # expire_on_rollback=False. This allow templates to reuse
            # request.instance object and joined object without triggering lazy
            # load.
            g.db_session.expunge_all()
            g.db_session.rollback()
        else:
            g.db_session.commit()

        g.db_session.close()
        del g.db_session


class APIKeyMiddleware(object):
    # Flask extension validating API key header

    def __init__(self, app):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.apikey = self
        app.before_request(self.before)

    def before(self):
        g.apikey = None

        if 'Authorization' not in request.headers:
            return

        remote_addr = ip_address(request.remote_addr)
        if not any((
                remote_addr in ip_network(cidr)
                for cidr in
                self.app.temboard.config.auth.allowed_ip
        )):
            logger.debug("Authorization ignored for IP %s.", remote_addr)
            return

        try:
            scheme, secret = request.headers['Authorization'].split(None, 1)
        except TypeError:
            abort(400, "Malformed Authorization header")

        if scheme != 'Bearer':
            logger.debug("Ignoring Authorization scheme %s.", scheme)
            return

        key = g.db_session.scalar(ApiKeys.select_secret(secret))
        if not key:
            abort(403, "Unknown API Key.")

        if key.expired:
            abort(403, "Expired API key.")

        logger.debug(
            "Accepted API key from HTTP Header, client IP %s.", remote_addr)
        g.apikey = key


class AuthMiddleware(object):
    # Flask extension enforcing authentication

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.user = self
        app.before_request(self.before)

    def before(self):
        func = self.app.view_functions[request.endpoint]

        apikey_allowed = getattr(func, '__apikey_allowed', False)
        if apikey_allowed and g.apikey:
            logger.debug("Endpoint authorized by API key.")
            return

        anonymous_allowed = getattr(func, '__anonymous_allowed', False)
        if not anonymous_allowed and g.current_user is None:
            logger.debug("Refusing anonymous access.")
            abort(403)

        admin_required = getattr(func, '__admin_required', False)
        if admin_required and not g.current_user.is_admin:
            logger.debug("Refusing access to non-admin user.")
            abort(403)


class UserMiddleware(object):
    # Flask extension to load current user.

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.user = self
        app.before_request(self.before)

    def before(self):
        g.current_user = None
        if 'temboard' in request.cookies:
            g.current_user = self.load_user_from_tornado_secure_cookie()
        if getattr(g, 'apikey', None):
            g.current_user = StubRole('temboard')

    def load_user_from_tornado_secure_cookie(self):
        cookie = decode_signed_value(
            self.app.temboard.config.temboard.cookie_secret,
            'temboard',
            request.cookies['temboard'],
        )
        cookie = cookie.decode('utf-8')
        return get_role_by_cookie(g.db_session, cookie)


def anonymous_allowed(func):
    # Decorator marking a route as public.
    func.__anonymous_allowed = True
    return func


def apikey_allowed(func):
    # Decorator allowing a route by apikey auth
    func.__apikey_allowed = True
    return func
