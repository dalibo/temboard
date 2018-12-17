# coding: utf-8
from __future__ import absolute_import

import functools
import json
import logging
import os

from tornado import web as tornadoweb
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode
from tornado.gen import coroutine
from tornado.web import (
    Application as TornadoApplication,
    HTTPError,
    RequestHandler,
)
from tornado.template import Loader as TemplateLoader

from .application import (
    get_instance,
    get_role_by_cookie,
)
from .model import Session as DBSession
from .temboardclient import (
    TemboardError,
    temboard_profile,
    temboard_get_notifications,
    temboard_request,
)


logger = logging.getLogger(__name__)


class Response(object):
    def __init__(
            self, status_code=200, headers=None, secure_cookies=None,
            body=None,):
        self.status_code = status_code
        self.headers = headers or {}
        self.secure_cookies = secure_cookies or {}
        self.body = body or u''


class Redirect(Response, Exception):
    def __init__(self, location, permanent=False, secure_cookies=None):
        super(Redirect, self).__init__(
            status_code=301 if permanent else 302,
            headers={'Location': location},
            body=u'Redirected to %s' % location,
            secure_cookies=secure_cookies,
        )


class TemplateRenderer(object):
    # Flask-like HTML render function, without thread local.

    def __init__(self, path):
        self.loader = TemplateLoader(path)

    def __call__(self, template, **data):
        return Response(body=self.loader.load(template).generate(**data))


template_path = os.path.realpath(__file__ + '/../templates')
render_template = TemplateRenderer(template_path)


class CallableHandler(RequestHandler):
    # Adapt flask-like callable in Tornado Handler API.

    @property
    def executor(self):
        # To enable @run_on_executor methods, we must have executor property.
        return self.application.executor

    def initialize(self, callable_, blueprint=None, methods=None, logger=None):
        self.callable_ = callable_
        self.logger = logger or logging.getLogger(__name__)
        self.request.blueprint = blueprint
        self.request.config = self.application.config
        # run_on_executor searches for `executor` attribute of first argument.
        # Thus, we bind executor to request object.
        self.request.executor = self.executor
        self.request.handler = self
        self.SUPPORTED_METHODS = methods or ['GET']

    def get_current_user(self):
        cookie = self.get_secure_cookie('temboard')
        if not cookie:
            return

        try:
            return get_role_by_cookie(self.db_session, cookie)
        except Exception as e:
            self.logger.error("Failed to get role from cookie: %s ", e)

    @run_on_executor
    def prepare(self):
        # This should be middlewares
        self.request.db_session = self.db_session = DBSession()
        self.request.current_user = self.current_user

    @run_on_executor
    def on_finish(self):
        # This should be middlewares
        self.request.db_session.commit()
        self.request.db_session.close()
        del self.request.db_session

    @coroutine
    def get(self, *args, **kwargs):
        try:
            response = yield self.callable_(self.request, *args, **kwargs)
        except Redirect as response:
            pass

        if response is None:
            response = u''
        if isinstance(response, (dict, unicode)):
            response = Response(body=response)
        self.write_response(response)

    # Let's use one handler for all supported methods.
    post = get

    def write_response(self, response):
        # Should be in a middleware.
        if response.status_code in (301, 302, 401):
            response.secure_cookies['referer_uri'] = self.request.uri

        self.set_status(response.status_code)
        for k, v in response.headers.items():
            if not isinstance(v, list):
                v = [v]
            for v1 in v:
                self.add_header(k, v1)

        for k, v in response.secure_cookies.items():
            self.set_secure_cookie(k, v, expires_days=30)

        self.finish(response.body)


class InstanceHelper(object):
    # This helper class implements all operations related to instance dedicated
    # request.

    INSTANCE_PARAMS = r'/(.*)/([0-9]{1,5})'
    PROXY_PREFIX = r'/proxy' + INSTANCE_PARAMS
    SERVER_PREFIX = r'/server' + INSTANCE_PARAMS

    @classmethod
    def add_middleware(cls, callable_):
        # Wraps an HTTP handler callable related to a Postgres instance

        @functools.wraps(callable_)
        def middleware(request, address, port, *args):
            # Swallow adddress and port arguments.
            request.instance = cls(request)
            request.instance.fetch_instance(address, port)
            return callable_(request, *args)

        return middleware

    def __init__(self, request):
        self.request = request
        self._xsession = False

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.instance.hostname)

    def check_active_plugin(self, name):
        '''
        Ensure that the plugin is active for given instance
        '''
        if name not in [p.plugin_name for p in self.instance.plugins]:
            raise HTTPError(408, "Plugin not activated.")

    def fetch_instance(self, address, port):
        self.instance = get_instance(self.request.db_session, address, port)
        if not self.instance:
            raise HTTPError(404)

    @property
    def cookie_name(self):
        return 'temboard_%s_%s' % (
            self.instance.agent_address, self.instance.agent_port,
        )

    @property
    def xsession(self):
        if self._xsession is False:
            self._xsession = self.request.handler.get_secure_cookie(
                self.cookie_name)
        return self._xsession

    def redirect_login(self):
        login_url = "/server/%s/%s/login" % (
            self.instance.agent_address, self.instance.agent_port)
        raise Redirect(location=login_url)

    def proxy(self, method, path, body=None):
        url = 'https://%s:%s%s' % (
            self.instance.agent_address,
            self.instance.agent_port,
            path,
        )

        headers = {}
        xsession = self.xsession
        if xsession:
            headers['X-Session'] = xsession

        logger.debug("Proxying %s %s.", method, url)
        try:
            body = temboard_request(
                self.request.config.temboard.ssl_ca_cert_file,
                method=method,
                url=url,
                headers=headers,
                data=body,
            )
        except Exception as e:
            logger.error("Proxied request failed: %s", e)
            raise HTTPError(500)
        return Response(
            status_code=200,
            body=json.loads(body),
        )

    def require_xsession(self):
        if not self.xsession:
            self.redirect_login()
        return self.xsession

    def get_profile(self):
        try:
            return temboard_profile(
                self.request.config.temboard.ssl_ca_cert_file,
                self.instance.agent_address,
                self.instance.agent_port,
                self.require_xsession(),
            )
        except TemboardError as e:
            if 401 == e.code:
                self.redirect_login()
            logger.error('Instance error: %s', e)
            raise HTTPError(500)

    def get_notifications(self):
        return temboard_get_notifications(
            self.request.config.temboard.ssl_ca_cert_file,
            self.instance.agent_address,
            self.instance.agent_port,
            self.require_xsession(),
        )


class Blueprint(object):
    def __init__(self, plugin_name=None):
        self.plugin_name = plugin_name
        self.rules = []

    def add_rules(self, rules):
        self.rules.extend(rules)

    def generic_proxy(self, url, methods=None):
        # Pass-through implementation for /proxy/address/port/…
        url = r'(%s)' % url

        @self.instance_proxy(url, methods)
        def generic_instance_proxy(request, path):
            if request.blueprint and request.blueprint.plugin_name:
                request.instance.check_active_plugin(
                    request.blueprint.plugin_name)
            body = json_decode(request.body) if request.body else None
            return request.instance.proxy(request.method, path, body=body)

    def instance_proxy(self, url, methods=None):
        # decorator for /proxy/address/port/… handlers.
        url = InstanceHelper.PROXY_PREFIX + url
        return self.route(url, methods=methods, with_instance=True)

    def instance_route(self, url, methods=None):
        # Helper to declare a route with instance URL prefix and middleware.
        return self.route(
            url=InstanceHelper.SERVER_PREFIX + url,
            methods=methods,
            with_instance=True,
        )

    def route(self, url, methods=None, with_instance=False):
        # Implements flask-like route registration of a simple synchronous
        # callable.

        def decorator(func):
            logger_name = func.__module__ + '.' + func.__name__

            if with_instance:
                func = InstanceHelper.add_middleware(func)

            @run_on_executor
            def wrapper(request, *args):
                try:
                    return func(request, *args)
                except Redirect:
                    raise
                except HTTPError as e:
                    code = e.status_code
                    message = str(e)
                except Exception as e:
                    # Since async traceback is useless, spit here traceback and
                    # mock HTTPError(500).
                    logger.exception("Unhandled Error:")
                    code = 500
                    message = str(e)
                response = render_template(
                    'error.html',
                    nav=True, instance=request.instance,
                    role=request.current_user,
                    code=code, error=message,
                )
                response.status_code = code
                return response
            rules = [(
                url, CallableHandler, dict(
                    blueprint=self,
                    callable_=wrapper,
                    methods=methods or ['GET'],
                    logger=logging.getLogger(logger_name),
                ),
            )]
            self.add_rules(rules)
            return func

        return decorator


class WebApplication(TornadoApplication, Blueprint):
    def __init__(self, *a, **kwargs):
        super(WebApplication, self).__init__(*a, **kwargs)

    def configure(self, **settings):
        # Runtime configuration of application.
        #
        # This way, we can initialize app at import time to register handlers.
        # Then configure it at run time once configuration is parsed.

        self.settings.update(settings)

        # This comes from Tornado's __init__
        if self.settings.get('debug'):
            self.settings.setdefault('autoreload', True)
            self.settings.setdefault('compiled_template_cache', False)
            self.settings.setdefault('static_hash_cache', False)
            self.settings.setdefault('serve_traceback', True)

    def add_rules(self, rules):
        if hasattr(self, 'wildcard_router'):  # Tornado 4.5+
            self.wildcard_router.add_rules(rules)
        elif not self.handlers:
            self.add_handlers(r'.*$', rules)
        else:
            rules = [tornadoweb.URLSpec(*r) for r in rules]
            self.handlers[0][1].extend(rules)


# Global app instance for registration of core handlers.
app = WebApplication()
# Hijack tornado.web access_log to log request in temboardui namespace.
tornadoweb.access_log = logging.getLogger('temboardui.access')
