# Flask WSGI app is served by Tornado's fallback handler.

import contextlib
import functools
import json
import logging
import os
from ipaddress import ip_address, ip_network

import jinja2
import werkzeug.exceptions
from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    g,
    jsonify,
    make_response,
    render_template,
    request,
)
from tornado.web import decode_signed_value
from werkzeug.exceptions import HTTPException

from ..agentclient import TemboardAgentClient
from ..application import get_instance, get_role_by_cookie
from ..model import Session
from ..model.orm import ApiKey, StubRole
from ..toolkit.utils import utcnow
from .tornado import serialize_querystring
from .vitejs import ViteJSExtension

logger = logging.getLogger(__name__)


class InstanceProxyBlueprint(Blueprint):
    # Pass-through implementation for /proxy/address/port/…
    def generic_proxy(self, url, method="GET"):
        # Register an unique endpoint name for each proxy.
        # Without this, every generic proxy routes would share the same
        # endpoint, leading to :
        # View function mapping is overwriting an existing endpoint
        endpoint = f"generic_instance_proxy_{url.replace('/', '_')}_{method}"

        @self.route(url, methods=[method], endpoint=endpoint)
        def generic_instance_proxy(**_):
            # Skip the first three segments proxy/adress/port
            *_, path = request.path.split("/", 4)
            path = f"/{path}"

            response = current_app.instance.request(
                path,
                method=method,
                body=request.get_json() if method == "POST" else None,
                query=request.args.to_dict(),
            )
            return jsonify(response.json())


# InstanceMiddleware extension controls request context for the following
# blueprint routes.
instance_proxy = InstanceProxyBlueprint(
    "instance_proxy", __name__, url_prefix="/proxy/<address>/<port>"
)

instance_routes = Blueprint(
    "instance_routes", __name__, url_prefix="/server/<address>/<port>"
)


def create_app(temboard_app):
    app = Flask("temboardui")
    app.start_time = utcnow()
    app.config["DEBUG"] = app.config["TESTING"] = "DEBUG" in os.environ
    app.temboard = temboard_app
    app.static_folder = "static/dist"
    app.static_url_path = "/static"
    app.template_folder = "templates/flask"
    app.jinja_env.undefined = jinja2.StrictUndefined
    app.jinja_env.trim_blocks = True
    SQLAlchemy(app)
    APIKeyMiddleware(app)
    UserMiddleware(app)
    AuthMiddleware(app)
    # DEPRECATED: Seems required for old Flask only.
    for code in werkzeug.exceptions.default_exceptions.keys():
        app.register_error_handler(code, error_handler)
    app.register_error_handler(Exception, error_handler)

    # unsafe-eval is for jquery. unsafe-inline because we have
    # script tags in templates.
    csp = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data:"
    if "VITEJS" in os.environ:
        csp += " localhost:5173 ws:"

    @app.after_request
    def add_csp(resp):
        resp.headers["Content-Security-Policy"] = csp
        return resp

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


def error_handler(e):
    status_code = e.code if isinstance(e, HTTPException) else None

    error = str(e) or repr(e)
    if hasattr(e, "description"):  # From Flask HTTPException.
        error = e.description

    if status_code is None:
        logger.exception("Unhandled error:")
        status_code = 500
        if current_app.temboard.debug:
            error = "Internal temBoard error. Retry later or contact administrator."
    elif status_code < 500:
        logger.warning("User error: %s", error)
    else:
        logger.error("Fatal error: %s", error)

    if request.path.endswith(".csv"):
        return "", status_code
    elif is_json(request.path):
        response = jsonify(error=error)
        response.status_code = status_code
        return response

    template_vars = {}
    if hasattr(g, "instance"):
        template_vars["instance"] = g.instance
    if status_code in (401, 403, 404):
        template = f"{status_code}.html"
    else:
        template = "error.html"

    return render_template(template, message=error, code=status_code, **template_vars)


def is_json(path):
    return (
        path.startswith("/json") or path.startswith("/proxy") or path.endswith(".json")
    )


class SQLAlchemy:
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
        # Expunge objects to implement expire_on_rollback=False.
        # This allow templates to reuse request.instance object and joined object
        # without triggering lazy load.
        g.db_session.expunge_all()
        g.db_session.close()
        del g.db_session


class APIKeyMiddleware:
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

        if "Authorization" not in request.headers:
            return

        remote_addr = ip_address(request.remote_addr)
        if not any(
            remote_addr in ip_network(cidr)
            for cidr in self.app.temboard.config.auth.allowed_ip
        ):
            logger.debug("Authorization ignored for IP %s.", remote_addr)
            return

        try:
            scheme, secret = request.headers["Authorization"].split(None, 1)
        except TypeError:
            abort(400, "Malformed Authorization header")

        if scheme != "Bearer":
            logger.debug("Ignoring Authorization scheme %s.", scheme)
            return

        key = ApiKey.select_secret(secret).with_session(g.db_session).scalar()
        if not key:
            abort(403, "Unknown API Key.")

        if key.expired:
            abort(403, "Expired API key.")

        logger.debug("Accepted API key from HTTP Header, client IP %s.", remote_addr)
        g.apikey = key


class AuthMiddleware:
    # Flask extension enforcing authentication

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.user = self
        app.before_request(self.before)

        @app.context_processor
        def inject_user():
            return dict(role=g.current_user)

    def before(self):
        if request.url_rule and request.url_rule.rule.startswith("/static"):
            # Skip Auth for static files.
            return

        func = self.app.view_functions.get(request.endpoint)
        if not func:
            abort(404)

        apikey_allowed = getattr(func, "__apikey_allowed", False)
        if apikey_allowed and g.apikey:
            logger.debug("Endpoint authorized by API key.")
            return

        anonymous_allowed = getattr(func, "__anonymous_allowed", False)
        if not anonymous_allowed and g.current_user is None:
            logger.debug("Refusing anonymous access.")
            abort(401)

        admin_required = getattr(func, "__admin_required", False)
        if admin_required and not g.current_user.is_admin:
            logger.debug("Refusing access to non-admin user.")
            abort(403)


class UserMiddleware:
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
        if "temboard" in request.cookies:
            g.current_user = self.load_user_from_tornado_secure_cookie()
        if getattr(g, "apikey", None):
            g.current_user = StubRole("temboard")

    def load_user_from_tornado_secure_cookie(self):
        cookie = decode_signed_value(
            self.app.temboard.config.temboard.cookie_secret,
            "temboard",
            request.cookies["temboard"],
        )
        if cookie:
            cookie = cookie.decode("utf-8")
            try:
                return get_role_by_cookie(g.db_session, cookie)
            except Exception as e:
                logger.error("Failed to load user from cookie: %s", e)


class InstanceMiddleware:
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
        app.register_blueprint(instance_routes)
        brf = app.before_request_funcs
        brf[instance_proxy.name] = [self.load_instance_before_request]
        brf[instance_routes.name] = [self.load_instance_before_request]

        @app.teardown_request
        def teardown_instance(*_):
            if hasattr(g, "instance"):
                delattr(g, "instance")

        @app.context_processor
        def context_processor():
            if not hasattr(g, "instance"):
                return {}
            return dict(instance=g.instance)

    def load_instance_before_request(self):
        address = request.view_args.pop("address")
        port = request.view_args.pop("port")

        g.instance = get_instance(g.db_session, address, port)
        if not g.instance:
            abort(404)

        func = self.app.view_functions.get(request.endpoint)
        apikey_allowed = g.apikey and getattr(func, "__apikey_allowed", False)
        user_allowed = (
            g.current_user
            and g.db_session.execute(
                g.instance.has_dba(g.current_user.role_name)
            ).scalar()
        )
        if not apikey_allowed and not user_allowed:
            abort(403)
        g.instance.status = None
        prefix = current_app.blueprints[request.blueprint].url_prefix
        request.instance_path = request.url_rule.rule.replace(prefix, "")

    def fetch_status(self):
        try:
            data = json.load(self.request("/status"))
        except Exception as e:
            # agent is unreachable we forge a status response
            logger.error("Failed to fetch status: %s", e)
            data = {
                "temboard": {"status": "unreachable"},
                "postgres": {"status": "unreachable", "pending_restart": False},
                "system": {"status": "unreachable"},
            }
        g.instance.status = data

    def client(self):
        return TemboardAgentClient.factory(
            current_app.temboard.config,
            g.instance.agent_address,
            g.instance.agent_port,
            g.current_user.role_name,
        )

    def request(self, path, method="GET", query=None, body=None):
        client = self.client()

        pathinfo = path
        if query:
            pathinfo += "?" + serialize_querystring(query)

        try:
            response = client.request(method=method, path=pathinfo, body=body)
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
        agent_response = self.request(path=request.instance_path, method=request.method)
        response = make_response(agent_response.read())
        h = "Content-Type"
        response.headers[h] = agent_response.headers[h]
        return response

    def check_active_plugin(self, name):
        """
        Ensure that the plugin is active for given instance
        """
        if name not in [p.plugin_name for p in g.instance.plugins]:
            raise abort(408, "Plugin %s not activated." % name)


def anonymous_allowed(func):
    # Decorator marking a route as public.
    func.__anonymous_allowed = True
    return func


def apikey_allowed(func):
    # Decorator allowing a route by apikey auth
    func.__apikey_allowed = True
    return func


def admin_required(func):
    # Similar to flask_security.roles_required, but limited to admin role.
    func.__admin_required = True
    return func


def transaction(func):
    # Flask is not reliable for catching exception in extension.
    # Instead, use an explicit decorator to deduplicate transaction handling.
    # Use this in routes modifying database.
    @functools.wraps(func)
    def autocommit_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            g.db_session.rollback()
            raise
        finally:
            g.db_session.commit()

    return autocommit_wrapper


@contextlib.contextmanager
def validating():
    # Translate ValueError to HTTP 408
    try:
        yield
    except ValueError as e:
        raise abort(408, str(e))
