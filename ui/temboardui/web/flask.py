import logging

from flask import Flask, abort, g, request, redirect, jsonify
from werkzeug.exceptions import HTTPException
from tornado.web import decode_signed_value

from ..model import Session
from ..application import (
    get_role_by_cookie,
)


logger = logging.getLogger(__name__)


def create_app(temboard_app):
    app = Flask('temboardui', static_folder=None)
    app.temboard = temboard_app
    SQLAlchemy(app)
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


class AuthMiddleware(object):
    # Flask extension enforcing authentication

    def unauthorized(self):
        if g.current_user:
            abort(403)
        return redirect('/login')

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.user = self
        app.before_request(self.before)

    def before(self):
        func = self.app.view_functions[request.endpoint]

        anonymous_allowed = getattr(func, '__anonymous_allowed', False)
        if not anonymous_allowed and g.current_user is None:
            logger.debug("Redirecting anonymous to /login.")
            return redirect('/login')

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
