# coding: utf-8

import imp
import logging.config
import os
import pkg_resources
import socket
import sys
from argparse import (
    ArgumentParser,
    SUPPRESS as UNDEFINED_ARGUMENT,
    _VersionAction,
)
from concurrent.futures import ThreadPoolExecutor

import tornado.ioloop
import tornado.web
from tornado import autoreload

from .model import configure as configure_db_session, check_schema
from .toolkit import taskmanager
from .toolkit import validators as v
from .toolkit.app import define_core_arguments
from .toolkit.configuration import OptionSpec
from .toolkit.errors import UserError
from .toolkit.proctitle import ProcTitleManager
from .toolkit.services import (
    Service,
    ServicesManager,
)
from .toolkit.tasklist.sqlite3_engine import TaskListSQLite3Engine
from .web import Error404Handler, app

from .daemon import daemonize
from .pluginsmgmt import load_plugins
from .autossl import AutoHTTPSServer
from .toolkit.app import BaseApplication
from .version import __version__, format_version, inspect_versions


logger = logging.getLogger('temboardui')


def legacy_bootstrap(config):
    # Compat with legacy load_plugins
    config.plugins = {}

    autoreload.watch(config.temboard.configfile)

    # Run temboard as a background daemon.
    if config.temboard.daemonize:
        daemonize(config.temboard.pidfile, config)

    return config


def legacy_enable_plugins(self, plugin_names):
    # Load and enable legacy plugins in tornado app.
    plugins = load_plugins(plugin_names, self.config)
    plugins_conf = dict()
    self.workersets = []
    self.loaded_plugins = []
    for key, val in plugins.iteritems():
        self.add_rules(val['routes'])
        plugins_conf[key] = val['configuration']
        if val['workers']:
            self.workersets.append(val['workers'])
        if key not in self.loaded_plugins:
            self.loaded_plugins.append(key)
    return plugins_conf


def bootstrap_tornado_app(app, config):
    app.config = config

    base_path = os.path.dirname(__file__)
    # Load handlers
    __import__('temboardui.handlers.home')
    __import__('temboardui.handlers.notification')
    __import__('temboardui.handlers.settings.group')
    __import__('temboardui.handlers.settings.instance')
    __import__('temboardui.handlers.settings.user')
    __import__('temboardui.handlers.settings.notifications')
    __import__('temboardui.handlers.user')

    app.configure(
        cookie_secret=config.temboard['cookie_secret'],
        debug=config.logging.debug,
        template_path=base_path + "/templates",
        default_handler_class=Error404Handler,
    )

    return app


def finalize_tornado_app(app, config, plugins):
    base_path = os.path.dirname(__file__)
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
        })
    ]

    config.plugins = legacy_enable_plugins(app, plugins)
    # Append rules *after* plugins because plugins shares same namespace for
    # static rules, i.e. /js/.* is a fallback for /js/dashboard/.*.
    app.add_rules(handlers)


def map_pgvars(environ):
    pgvar_map = dict(
        PGHOST='TEMBOARD_REPOSITORY_HOST',
        PGPORT='TEMBOARD_REPOSITORY_PORT',
        PGUSER='TEMBOARD_REPOSITORY_USER',
        PGPASSWORD='TEMBOARD_REPOSITORY_PASSWORD',
        PGDATABASE='TEMBOARD_REPOSITORY_DBNAME',
    )
    mapped = environ.copy()
    for pgvar, tbvar in pgvar_map.items():
        if tbvar in environ:
            continue

        try:
            mapped[tbvar] = environ[pgvar]
            logger.debug("Read %s from environ.", pgvar)
        except KeyError:
            pass

    return mapped


class SchedulerService(taskmanager.SchedulerService):
    def apply_config(self):
        super(SchedulerService, self).apply_config()
        if self.scheduler:
            # Set legacy config context.
            self.scheduler.set_context(
                'config',
                {
                    # Wrap settings in dict for JSON serializable.
                    'plugins': dict(self.app.config.plugins),
                    'temboard': dict(self.app.config.temboard),
                    'repository': dict(self.app.config.repository),
                }
            )


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

    def serve(self):
        with self:
            # Automatically reload modified modules (from Tornado's
            # Application.__init__). This code must be done here *after*
            # daemonize, because it instanciates ioloop for current PID.
            if self.app.webapp.settings.get('autoreload'):
                autoreload.start()

            logger.info(
                "Serving temboardui on https://%s:%d",
                self.app.config.temboard.address,
                self.app.config.temboard.port)
            tornado.ioloop.IOLoop.instance().start()


class VersionAction(_VersionAction):
    def __call__(self, parser, *_):
        print(format_version().strip())
        parser.exit()


def define_arguments(parser):
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
    yield OptionSpec(s, 'cookie_secret', validator=cookie_secret)
    home = os.environ.get('HOME', '/var/lib/temboard')
    yield OptionSpec(s, 'home', default=home, validator=v.writeabledir)

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


class TemboardApplication(BaseApplication):
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
    PROGRAM = 'temboard'
    REPORT_URL = "https://github.com/dalibo/temboard/issues"
    VERSION = __version__

    def filter_plugins(self):
        # Returns two lists of plugin names from config.temboard.plugins, the
        # first list is legacy plugins, the second is external plugins.

        legacy_plugins = []
        ep_plugins = []

        path = os.path.dirname(__file__) + '/plugins'

        logger.debug("Looping over all plugins.")
        for name in self.config.temboard.plugins:
            if any(pkg_resources.iter_entry_points(self.with_plugins, name)):
                logger.debug("%s is a new plugin.", name)
                ep_plugins.append(name)
            else:
                try:
                    fp, _, _ = imp.find_module(name, [path])
                except ImportError:
                    raise UserError("Missing plugin: %s." % name)
                else:
                    legacy_plugins.append(name)
                    logger.debug("%s is a legacy plugin.", name)

        return legacy_plugins, ep_plugins

    def apply_config(self):
        bootstrap_tornado = not hasattr(self, 'webapp')
        if bootstrap_tornado:
            # For now, just create web app once. One time, we'll be able to
            # unload plugin routes.
            self.webapp = bootstrap_tornado_app(app, self.config)
            self.webapp.executor = ThreadPoolExecutor(12)
            self.webapp.temboard_app = self

        legacy_plugins, ep_plugins = self.filter_plugins()
        self.config.temboard.plugins = ep_plugins

        super(TemboardApplication, self).apply_config()

        finalize_tornado_app(app, self.config, plugins=legacy_plugins)

        self.webapp.engine = configure_db_session(self.config.repository)

    def main(self, argv, environ):

        # C O N F I G U R A T I O N

        parser = ArgumentParser(
            prog='temboard',
            description="temBoard web UI.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_arguments(parser)
        args = parser.parse_args(argv)
        environ = map_pgvars(environ)
        self.bootstrap(args=args, environ=environ)

        setproctitle = ProcTitleManager(prefix='temboard: ')
        setproctitle.setup()

        versions = inspect_versions()
        logger.info(
            "Running on %s %s.",
            versions['distname'], versions['distversion'])
        logger.info(
            "Using Python %s (%s).",
            versions['python'], versions['pythonbin'])
        logger.info(
            "Using Psycopg2 %s, Tornado %s and SQLAlchemy %s",
            versions['psycopg2'], versions['tornado'], versions['sqlalchemy'],
        )
        logging.getLogger('alembic').setLevel(logging.WARN)
        # Manage logging_debug default until we use toolkit OptionSpec.
        legacy_bootstrap(self.config)

        services = ServicesManager()

        # T A S K   M A N A G E R

        task_queue = taskmanager.Queue()
        event_queue = taskmanager.Queue()

        self.worker_pool = taskmanager.WorkerPoolService(
            app=self, name=u'worker pool',
            task_queue=task_queue, event_queue=event_queue,
            setproctitle=setproctitle,
        )
        self.scheduler = SchedulerService(
            app=self, name=u'scheduler',
            task_queue=task_queue, event_queue=event_queue,
            setproctitle=setproctitle,
        )

        # TaskList engine setup must be done before we load the plugins
        self.scheduler.task_list_engine = TaskListSQLite3Engine(
            os.path.join(self.config.temboard['home'], 'server_tasks.db')
        )

        self.apply_config()

        check_schema(self.config)

        self.worker_pool.apply_config()
        services.add(self.worker_pool)

        for wset in self.webapp.workersets:
            self.worker_pool.add(wset)

        self.scheduler.apply_config()
        services.add(self.scheduler)

        # H T T P   S E R V E R

        webservice = TornadoService(
            app=self, name=u'web', services=services,
            setproctitle=setproctitle,
        )
        with services:
            webservice.run()


main = TemboardApplication(
    specs=list_options_specs(),
    with_plugins="temboard.plugins",
)


if __name__ == "__main__":
    sys.exit(main())
