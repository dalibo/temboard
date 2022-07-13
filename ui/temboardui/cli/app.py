# coding: utf-8

from __future__ import print_function

from builtins import str
import logging.config
import os
import socket
import sys
from argparse import _VersionAction
from concurrent.futures import ThreadPoolExecutor
from textwrap import dedent

from flask import current_app

import tornado.ioloop
import tornado.web
from tornado.wsgi import WSGIContainer
from tornado import autoreload

from ..autossl import AutoHTTPSServer
from ..model import configure as configure_db_session, queries
from ..toolkit import taskmanager, validators as v
from ..toolkit.app import (
    BaseApplication,
    define_core_arguments,
)
from ..toolkit.configuration import OptionSpec, MergedConfiguration
from ..toolkit.errors import UserError
from ..toolkit.proctitle import ProcTitleManager
from ..toolkit.services import Service
from ..toolkit.signing import load_private_key
from ..toolkit.tasklist.sqlite3_engine import TaskListSQLite3Engine
from ..version import __version__, format_version, inspect_versions
from ..web.tornado import Error404Handler, app as webapp


logger = logging.getLogger('temboardui')


class TemboardApplication(BaseApplication):
    PROGRAM = 'temboard'
    VERSION = __version__

    DEFAULT_CONFIGFILES = [
        '/etc/temboard/temboard.conf',
        'temboard.conf',
    ]
    DEFAULT_PLUGINS = [
        'activity',
        'dashboard',
        'monitoring',
        'pgconf',
        'maintenance',
        'statements',
    ]

    def __init__(self, *a, **kw):
        super(TemboardApplication, self).__init__(*a, **kw)
        self.config = TemboardUIConfiguration()

    def define_arguments(self, parser):
        define_core_arguments(parser)
        parser.add_argument(
            '-V', '--version',
            action=VersionAction,
            help='show version and exit',
        )
        parser.add_argument(
            '-d', '--daemon',
            action='store_true', dest='temboard_daemonize',
            help="Run in background.",
        )
        parser.add_argument(
            '-p', '--pid-file',
            action='store', dest='temboard_pidfile',
            help="PID file.", metavar='PIDFILE',
        )

        # Chain up for sub-commands arguments initialization.
        super(TemboardApplication, self).define_arguments(parser)

    def main(self, argv, environ):

        # C O N F I G U R A T I O N

        parser = self.create_parser(
            description=dedent("""\
            temBoard UI %s.

            COMMAND is optional. Default command is `serve`, the combined
            service. See available commands below.

            """) % __version__,
        )
        self.define_arguments(parser)

        args = parser.parse_args(argv)

        command_name = getattr(args, 'command_fullname', 'serve')
        command = self.commands[command_name]

        environ = map_pgvars(environ)
        self.bootstrap(args=args, environ=environ, service=command.is_service)
        self.log_versions()

        setproctitle = ProcTitleManager(prefix='temboard: ')
        setproctitle.setup()

        # T A S K   M A N A G E R

        task_queue = taskmanager.Queue()
        event_queue = taskmanager.Queue()

        self.worker_pool = taskmanager.WorkerPoolService(
            app=self, name=u'worker pool',
            task_queue=task_queue, event_queue=event_queue,
            setproctitle=setproctitle,
        )
        self.services.append(self.worker_pool)
        self.scheduler = taskmanager.SchedulerService(
            app=self, name=u'scheduler',
            task_queue=task_queue, event_queue=event_queue,
            setproctitle=setproctitle,
        )
        self.services.append(self.scheduler)

        self.webservice = TornadoService(
            app=self, name=u'web',
            setproctitle=setproctitle,
        )

        # TaskList engine setup must be done before we load the plugins
        self.scheduler.task_list_engine = TaskListSQLite3Engine(
            os.path.join(self.config.temboard['home'], 'server_tasks.db')
        )

        self.apply_config()

        return command.main(args)

    def apply_config(self):
        bootstrap_tornado = not hasattr(self, 'webapp')
        if bootstrap_tornado:
            # For now, just create web app once. One time, we'll be able to
            # unload plugin routes.
            self.webapp = bootstrap_tornado_app(webapp, self.config)
            self.webapp.executor = ThreadPoolExecutor(12)
            self.webapp.temboard_app = self

        super(TemboardApplication, self).apply_config()

        finalize_tornado_app(webapp, self.config)

        self.webapp.engine = configure_db_session(self.config.repository)

    def log_versions(self):
        versions = inspect_versions()
        logger.debug(
            "Running on %s %s.",
            versions['distname'], versions['distversion'])
        logger.debug(
            "Using Python %s (%s) and Tornado %s .",
            versions['python'], versions['pythonbin'], versions['tornado'])
        logger.debug(
            "Using libpq %s, Psycopg2 %s and SQLAlchemy %s .",
            versions['libpq'], versions['psycopg2'], versions['sqlalchemy'],
        )


class TemboardUIConfiguration(MergedConfiguration):
    def __init__(self, *a, **kw):
        MergedConfiguration.__init__(self, *a, **kw)  # PY2, use super.
        self._signing_key = None

    @property
    def signing_key(self):
        # Lazy load signing key.
        if not self._signing_key:
            self.load_signing_key()
        return self._signing_key

    def load_signing_key(self):
        path = self.temboard.signing_private_key
        logger.debug("Loading signing key from %s.", path)
        try:
            fo = open(path, 'rb')
        except OSError as e:
            raise UserError("Failed to load signing key: %s" % e)

        with fo:
            self._signing_key = load_private_key(fo.read())


def bootstrap_tornado_app(webapp, config):
    webapp.config = config

    base_path = os.path.dirname(os.path.dirname(__file__))
    # Load handlers
    __import__('temboardui.handlers.home')
    __import__('temboardui.handlers.notification')
    __import__('temboardui.handlers.settings.group')
    __import__('temboardui.handlers.settings.instance')
    __import__('temboardui.handlers.settings.user')
    __import__('temboardui.handlers.settings.notifications')
    __import__('temboardui.handlers.settings.metadata')
    __import__('temboardui.handlers.user')

    webapp.configure(
        cookie_secret=config.temboard['cookie_secret'],
        debug=config.logging.debug,
        template_path=base_path + "/templates",
        default_handler_class=Error404Handler,
    )

    return webapp


def finalize_tornado_app(webapp, config):
    base_path = os.path.dirname(os.path.dirname(__file__))
    handlers = [
        (r"/css/(.*)", tornado.web.StaticFileHandler, {
            'path': base_path + '/static/css'
        }),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {
            'path': base_path + '/static/js'
        }),
        (r"/images/(.*)", tornado.web.StaticFileHandler, {
            'path': base_path + '/static/images'
        }),
        (r"/fonts/(.*)", tornado.web.StaticFileHandler, {
            'path': base_path + '/static/fonts'
        }),
        # Path needs a (unused) path parameter, not used by subclass
        # SingleFileHandler.
        (r"/(signing.key)", SingleFileHandler, {
            'path': config.temboard.signing_public_key,
        }),
    ]

    # Append rules *after* plugins because plugins shares same namespace for
    # static rules, i.e. /js/.* is a fallback for /js/dashboard/.*.
    webapp.add_rules(handlers)

    # Fallback to Flask
    webapp.add_rules([
        (r"/.*", tornado.web.FallbackHandler, {
            'fallback': WSGIContainer(current_app.wsgi_app)}),
    ])


def map_pgvars(environ):
    pgvar_map = dict(
        PGHOST='TEMBOARD_REPOSITORY_HOST',
        PGPORT='TEMBOARD_REPOSITORY_PORT',
        PGUSER='TEMBOARD_REPOSITORY_USER',
        PGPASSWORD='TEMBOARD_REPOSITORY_PASSWORD',
        PGDATABASE='TEMBOARD_REPOSITORY_DBNAME',
    )
    mapped = environ.copy()
    for pgvar, tbvar in list(pgvar_map.items()):
        if tbvar in environ:
            continue

        try:
            mapped[tbvar] = environ[pgvar]
            logger.debug("Read %s from environ.", pgvar)
        except KeyError:
            pass

    return mapped


class TornadoService(Service):
    def setup(self):
        config = self.app.config
        ssl_ctx = {
            'certfile': config.temboard.ssl_cert_file,
            'keyfile': config.temboard.ssl_key_file,
        }
        server = AutoHTTPSServer(self.app.webapp, ssl_options=ssl_ctx)
        try:
            server.listen(
                config.temboard.port, address=config.temboard.address)
        except socket.error as e:
            logger.error("FATAL: " + str(e) + '. Quit')
            sys.exit(3)

    def autoreload_hook(self):
        if not self.services:
            return

        self.services.stop()
        try:
            self.services.check()
        except UserError as e:
            logger.debug("%s.", e)
        self.services.kill()
        try:
            self.services.check()
        except UserError as e:
            logger.debug("%s.", e)

    def iter_template_files(self):
        rootpkg = __import__(__name__)
        rootdir = rootpkg.__path__[0]
        for dirpath, dirnames, filenames in os.walk(rootdir):
            for filename in filenames:
                if filename.endswith('.html'):
                    yield dirpath + '/' + filename

    def serve(self):
        with self:
            # Automatically reload modified modules (from Tornado's
            # Application.__init__). This code must be done here *after*
            # daemonize, because it instanciates ioloop for current PID.
            if self.app.webapp.settings.get('autoreload'):
                self.setup_autoreload()
                autoreload.start()

            logger.info(
                "Serving temboardui on https://%s:%d",
                self.app.config.temboard.address,
                self.app.config.temboard.port)
            tornado.ioloop.IOLoop.instance().start()

    def setup_autoreload(self):
        autoreload.add_reload_hook(self.autoreload_hook)

        autoreload.watch(self.app.config.temboard.configfile)
        autoreload.watch(self.app.config.temboard.signing_public_key)
        autoreload.watch(self.app.config.temboard.signing_private_key)

        for path in self.iter_template_files():
            autoreload.watch(path)

        for path in queries.iter_queries_files(queries.QUERIESDIR):
            autoreload.watch(path)


class SingleFileHandler(tornado.web.StaticFileHandler):
    @classmethod
    def get_absolute_path(cls, root, *a):
        return root

    def validate_absolute_path(self, root, absolute_path):
        if not os.path.exists(absolute_path):
            logger.warning("Inexistant file %s", absolute_path)
            raise tornado.web.HTTPError(404)
        return absolute_path


class VersionAction(_VersionAction):
    def __call__(self, parser, *_):
        print(format_version().strip())
        parser.exit()


def cookie_secret(raw):
    length = len(raw)
    if length < 10:
        raise ValueError("cookie secret is shorter than 10 chars.")
    if length > 128:
        raise ValueError("cookie secret is longer than 128 chars.")
    return raw


def list_options_specs():
    s = 'temboard'
    # Manage plugin list here until we use plugin entrypoint.
    yield OptionSpec(
        s, 'plugins',
        default=TemboardApplication.DEFAULT_PLUGINS,
        validator=v.jsonlist,
    )
    yield OptionSpec(s, 'daemonize', default=False)
    yield OptionSpec(s, 'pidfile', default='/run/temboard.pid')
    yield OptionSpec(s, 'address', default='0.0.0.0', validator=v.address)
    yield OptionSpec(s, 'port', validator=v.port, default=8888)
    yield OptionSpec(
        s, 'ssl_cert_file',
        default=OptionSpec.REQUIRED, validator=v.file_)
    yield OptionSpec(
        s, 'ssl_key_file',
        default=OptionSpec.REQUIRED, validator=v.file_)
    yield OptionSpec(s, 'ssl_ca_cert_file', validator=v.file_)
    yield OptionSpec(
        s, 'signing_private_key',
        default='signing-private.pem', validator=v.path)
    yield OptionSpec(
        s, 'signing_public_key',
        default='signing-public.pem', validator=v.path)
    yield OptionSpec(s, 'cookie_secret', validator=cookie_secret)
    home = os.environ.get('HOME', '/var/lib/temboard')
    yield OptionSpec(s, 'home', default=home, validator=v.writeabledir)

    s = 'auth'
    yield OptionSpec(
        s, 'allowed_ip', default='127.0.0.0/8', validator=v.commalist)

    s = 'repository'
    yield OptionSpec(s, 'host', default='/var/run/postgresql')
    yield OptionSpec(s, 'instance', default='main')
    yield OptionSpec(s, 'port', default=5432, validator=v.port)
    yield OptionSpec(s, 'user', default='temboard')
    yield OptionSpec(s, 'password', default='temboard')
    yield OptionSpec(s, 'dbname', default='temboard')

    s = 'notifications'
    yield OptionSpec(s, 'smtp_host', default=None)
    yield OptionSpec(s, 'smtp_port', default=None, validator=v.port)
    yield OptionSpec(s, 'smtp_tls', default=False, validator=v.boolean)
    yield OptionSpec(s, 'smtp_login', default=None)
    yield OptionSpec(s, 'smtp_password', default=None)
    yield OptionSpec(s, 'smtp_from_addr', default=None)
    yield OptionSpec(s, 'twilio_account_sid', default=None)
    yield OptionSpec(s, 'twilio_auth_token', default=None)
    yield OptionSpec(s, 'twilio_from', default=None)

    s = 'monitoring'
    yield OptionSpec(s, 'purge_after', default=None, validator=v.nday)

    s = 'statements'
    yield OptionSpec(s, 'purge_after', default=7, validator=v.nday)


app = TemboardApplication(specs=list_options_specs())
