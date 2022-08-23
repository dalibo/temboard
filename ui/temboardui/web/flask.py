# Flask WSGI app is served by Tornado's fallback handler.

from __future__ import absolute_import

import logging
import os
from ipaddress import ip_address, ip_network

from flask import (
    Blueprint, Flask, abort, current_app, g, make_response, request, jsonify,
)
from werkzeug.exceptions import HTTPException
from tornado.web import decode_signed_value

from ..agentclient import TemboardAgentClient
from ..application import (
    get_instance,
    get_role_by_cookie,
)
from ..model import Session
from ..model.orm import ApiKeys, StubRole
from .tornado import serialize_querystring
from .vitejs import ViteJSExtension


logger = logging.getLogger(__name__)
# InstanceMiddleware extension controls request context for the following
# blueprint routes.
instance_proxy = Blueprint(
    "instance_proxy", __name__, url_prefix='/proxy/<address>/<port>',
)


def create_app(temboard_app):
    app = Flask('temboardui')
    app.config['DEBUG'] = app.config['TESTING'] = 'DEBUG' in os.environ
    app.temboard = temboard_app
    SQLAlchemy(app)
    APIKeyMiddleware(app)
    UserMiddleware(app)
    AuthMiddleware(app)
    app.errorhandler(Exception)(json_error_handler)
    ViteJSExtension(app)
    # finalize_app() must be called before serving, to enable configured
    # blueprints.
    return app


def finalize_app():
    # Configure Flask app after configuration is loaded.
    app = current_app

    # This middleware registers instance_proxy blueprint, loads g.instance
    # object and provides helpers in app.instance. instance is loaded only for
    # instance_proxy blueprint. instance_proxy must be registered after plugins
    # loading.
    InstanceMiddleware(app)

    return app


def json_error_handler(e):
    if isinstance(e, HTTPException):
        status_code = e.code
        if e.code < 500:
            logger.warning("User error: %s", e)
        else:
            logger.error("Fatal error: %s", e)
    else:
        status_code = 500
        logger.exception("Unhandled error:")
    response = jsonify(error=str(e) or repr(e))
    response.status_code = status_code
    return response


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

        key = (
            ApiKeys.select_secret(secret)
            .with_session(g.db_session)
            .scalar()
        )
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
        if request.url_rule and request.url_rule.rule.startswith('/static'):
            # Skip Auth for static files.
            return

        func = self.app.view_functions.get(request.endpoint)
        if not func:
            abort(404)

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
        if cookie:
            cookie = cookie.decode('utf-8')
            return get_role_by_cookie(g.db_session, cookie)


class InstanceMiddleware(object):
    # Flask extension providing instance helpers to view, setting up
    # instance_proxy middleware. Must be initialize once instance_proxy has its
    # routes.

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.instance = self
        app.register_blueprint(instance_proxy)
        brf = app.before_request_funcs
        brf[instance_proxy.name] = [
            self.load_instance_before_request,
        ]

    def load_instance_before_request(self):
        address = request.view_args.pop('address')
        port = request.view_args.pop('port')

        g.instance = get_instance(g.db_session, address, port)
        if not g.instance:
            abort(404)

        prefix = current_app.blueprints[request.blueprint].url_prefix
        request.instance_path = request.url_rule.rule.replace(prefix, "")

    def client(self):
        return TemboardAgentClient.factory(
            current_app.temboard.config,
            g.instance.agent_address,
            g.instance.agent_port,
            g.instance.agent_key,
            g.current_user.role_name,
        )

    def request(self, path, method='GET', query=None, body=None):
        client = self.client()

        pathinfo = path
        if query:
            pathinfo += "?" + serialize_querystring(query)

        try:
            response = client.request(
                method=method,
                path=pathinfo,
                body=body,
            )
            response.raise_for_status()
        except ConnectionError as e:
            abort(500, str(e))
        except TemboardAgentClient.Error as e:
            abort(e.response.status, e.message)
        except Exception as e:
            logger.error("Proxied request failed: %s", e)
            abort(500)
        else:
            return response

    def proxy(self):
        # Translate current Flask request to instance agent, translate the
        # response to a Flask response ready for return.
        agent_response = self.request(
            path=request.instance_path,
            method=request.method,
        )
        response = make_response(agent_response.read())
        h = 'Content-Type'
        response.headers[h] = agent_response.headers[h]
        return response


def anonymous_allowed(func):
    # Decorator marking a route as public.
    func.__anonymous_allowed = True
    return func


def apikey_allowed(func):
    # Decorator allowing a route by apikey auth
    func.__apikey_allowed = True
    return func
