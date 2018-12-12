# coding: utf-8
from __future__ import absolute_import

import functools
import logging
import os

from tornado import autoreload
from tornado import web as tornadoweb
from tornado.concurrent import run_on_executor
from tornado.gen import coroutine
from tornado.web import (
    Application as TornadoApplication,
    RequestHandler,
)
from tornado.template import Loader as TemplateLoader

from .application import get_role_by_cookie
from .model import Session as DBSession


logger = logging.getLogger(__name__)


class Response(object):
    def __init__(
            self, status_code=200, headers=None, secure_cookies=None,
            body=None,):
        self.status_code = status_code
        self.headers = headers or {}
        self.secure_cookies = secure_cookies or {}
        self.body = body or u''


class Redirect(Response):
    def __init__(self, location, permanent=False):
        super(Redirect, self).__init__(
            status_code=301 if permanent else 302,
            headers={'Location': location},
            body=u'Redirected to %s' % location,
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
    # Run synchronous callable in thread.

    def initialize(self, callable_, methods=None):
        name = callable_.__module__ + '.' + callable_.__name__
        self.logger = logging.getLogger(name)
        self.SUPPORTED_METHODS = methods or ['GET']

        callable_ = run_on_executor(callable_)
        # run_on_executor searches for `executor` attribute of first argument.
        # Thus, we bind executor to request object for run_on_executor and
        # hardcode here request as the first argument.
        self.request.executor = self.application.executor
        self.callable_ = functools.partial(callable_, self.request)

    @property
    def executor(self):
        # To enable @run_on_executor methods, we must have executor property.
        return self.application.executor

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
        response = yield self.callable_(*args, **kwargs)
        if response is None:
            response = u''
        if isinstance(response, unicode):
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


class WebApplication(TornadoApplication):
    def __init__(self, *a, **kwargs):
        super(WebApplication, self).__init__(*a, **kwargs)

    def configure(self, **settings):
        # Runtime configuration of application.
        #
        # This way, we can initialize app at import time to register handlers.
        # Then configure it at run time once configuration is parsed.

        self.settings.update(settings)

        # This comme from Tornado's __init__
        if self.settings.get('debug'):
            self.settings.setdefault('autoreload', True)
            self.settings.setdefault('compiled_template_cache', False)
            self.settings.setdefault('static_hash_cache', False)
            self.settings.setdefault('serve_traceback', True)

        # Automatically reload modified modules (from Tornado's __init__)
        if self.settings.get('autoreload'):
            autoreload.start()

    def route(self, url, methods=None):
        # Implements flask-like route registration of a simple synchronous
        # callable.

        def decorator(func):
            self.wildcard_router.add_rules([(
                url, CallableHandler, dict(
                    callable_=func,
                    methods=methods or ['GET'],
                ),
            )])
            return func

        return decorator


# Global app instance for registration of core handlers.
app = WebApplication()
# Hijack tornado.web access_log to log request in temboardui namespace.
tornadoweb.access_log = logging.getLogger('temboardui.access')
