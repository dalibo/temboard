# coding: utf-8

import logging.config
import os
import socket
import sys
from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT

import tornado.ioloop
import tornado.web
from tornado import autoreload

from sqlalchemy import create_engine

from .toolkit import taskmanager
from .toolkit import validators as v
from .toolkit.app import define_core_arguments
from .toolkit.configuration import OptionSpec
from .toolkit.services import (
    Service,
    ServicesManager,
)
from .toolkit.log import generate_logging_config
from .handlers.base import (
    BaseHandler,
    Error404Handler,
)
from .handlers.user import (
    AgentLoginHandler,
    LoginHandler,
    LoginJsonHandler,
    LogoutHandler,
)
from .handlers.home import (
    HomeHandler,
)
from .handlers.notification import (
    NotificationsHandler,
)
from .handlers.settings.user import (
    SettingsDeleteUserJsonHandler,
    SettingsUserHandler,
    SettingsUserJsonHandler,
)
from .handlers.settings.group import (
    SettingsDeleteGroupJsonHandler,
    SettingsGroupAllJsonHandler,
    SettingsGroupHandler,
    SettingsGroupJsonHandler,
)
from .handlers.settings.instance import (
    DiscoverInstanceJsonHandler,
    RegisterInstanceJsonHandler,
    SettingsDeleteInstanceJsonHandler,
    SettingsInstanceHandler,
    SettingsInstanceJsonHandler,
)

from .async import new_worker_pool
from .configuration import Configuration
from .errors import ConfigurationError
from .daemon import daemonize
from .pluginsmgmt import load_plugins
from .autossl import AutoHTTPSServer
from .toolkit.app import BaseApplication
from .utils import check_sqlalchemy_connectivity
from .version import __version__


logger = logging.getLogger('temboardui')


class CustomTornadoWebApp(tornado.web.Application):
    logger = None
    config = None
    loaded_plugins = []

    def set_logger(self, logger):
        self.logger = logger

    def set_config(self, config):
        self.config = config

    def load_plugins(self, plugin_names):
        plugins = load_plugins(plugin_names, self.config)
        plugins_conf = dict()
        self.loaded_plugins = []
        for key, val in plugins.iteritems():
            self.add_handlers(r'.*', val['routes'])
            plugins_conf[key] = val['configuration']
            if key not in self.loaded_plugins:
                self.loaded_plugins.append(key)
        return plugins_conf

    def log_request(self, handler):
        request_time = 1000.0 * handler.request.request_time()
        log_message = '%d %s %.2fms' % (handler.get_status(),
                                        handler._request_summary(),
                                        request_time)
        self.logger.info(log_message)

    def create_db_engine(self):
        dburi = "postgresql://{user}:{pwd}@:{p}/{db}?host={h}".format(
                    user=self.config.repository['user'],
                    pwd=self.config.repository['password'],
                    h=self.config.repository['host'],
                    p=self.config.repository['port'],
                    db=self.config.repository['dbname'],
                )
        self.engine = create_engine(dburi)
        try:
            check_sqlalchemy_connectivity(self.engine)
        except Exception as e:
            self.logger.warn("Connection to the database failed: %s", e)
            self.logger.warn("Please check your configuration.")
            sys.stderr.write("FATAL: %s\n" % e.message)
            exit(1)


def legacy_bootstrap(config):
    # Load configuration from the configuration file.
    legacy_config = Configuration()
    try:
        legacy_config.parsefile(config.temboard.configfile)
    except (ConfigurationError, ImportError) as e:
        sys.stderr.write("FATAL: %s\n" % e.message)
        exit(1)
    legacy_config.temboard = dict(config.temboard)

    logging.config.dictConfig(generate_logging_config(
        systemd='SYSTEMD' in os.environ,
        **config.logging
    ))
    logger.info("Starting main process.")
    autoreload.watch(config.temboard.configfile)

    # Run temboard as a background daemon.
    if config.temboard.daemonize:
        daemonize(config.temboard.pidfile, config)

    return legacy_config


def make_tornado_app(config, debug):
    base_path = os.path.dirname(__file__)
    handler_conf = {
        'ssl_ca_cert_file': config.temboard['ssl_ca_cert_file'],
        'template_path': None
    }
    application = CustomTornadoWebApp(
        [
            (r"/", BaseHandler, handler_conf),
            (r"/home", HomeHandler, handler_conf),
            (r"/login", LoginHandler, handler_conf),
            (r"/json/login", LoginJsonHandler, handler_conf),
            (r"/logout", LogoutHandler, handler_conf),
            # Manage users
            (r"/settings/users", SettingsUserHandler, handler_conf),
            (r"/json/settings/user$", SettingsUserJsonHandler, handler_conf),
            (r"/json/settings/user/([0-9a-z\-_\.]{3,16})$",
             SettingsUserJsonHandler, handler_conf),
            (r"/json/settings/delete/user$", SettingsDeleteUserJsonHandler,
             handler_conf),
            (r"/json/settings/all/group/(role|instance)$",
             SettingsGroupAllJsonHandler, handler_conf),
            # Manage groups (users & instances)
            (r"/settings/groups/(role|instance)$", SettingsGroupHandler,
             handler_conf),
            (r"/json/settings/group/(role|instance)$",
             SettingsGroupJsonHandler, handler_conf),
            (r"/json/settings/group/(role|instance)/([0-9a-z\-_\.]{3,16})$",
             SettingsGroupJsonHandler, handler_conf),
            (r"/json/settings/delete/group/(role|instance)$",
             SettingsDeleteGroupJsonHandler, handler_conf),
            # Manage instances
            (r"/settings/instances", SettingsInstanceHandler, handler_conf),
            (r"/json/settings/instance$", SettingsInstanceJsonHandler,
             handler_conf),
            (r"/json/register/instance$", RegisterInstanceJsonHandler,
             handler_conf),
            (r"/json/settings/instance/([0-9a-zA-Z\-\._:]+)/([0-9]{1,5})$",
             SettingsInstanceJsonHandler, handler_conf),
            (r"/json/settings/delete/instance$",
             SettingsDeleteInstanceJsonHandler, handler_conf),
            # Discover
            (r"/json/discover/instance/([0-9a-zA-Z\-\._:]+)/([0-9]{1,5})$",
             DiscoverInstanceJsonHandler, handler_conf),
            # Agent Login
            (r"/server/(.*)/([0-9]{1,5})/login", AgentLoginHandler,
             handler_conf),
            # Notifications
            (r"/server/(.*)/([0-9]{1,5})/notifications", NotificationsHandler,
             handler_conf),
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
        ],
        debug=debug,
        cookie_secret=config.temboard['cookie_secret'],
        template_path=base_path + "/templates",
        default_handler_class=Error404Handler)

    application.set_config(config)
    application.set_logger(logger)
    config.plugins = application.load_plugins(config.temboard['plugins'])
    application.create_db_engine()

    return application


class SchedulerService(taskmanager.SchedulerService):
    def apply_config(self):
        super(SchedulerService, self).apply_config()
        if self.scheduler:
            # Set legacy config context.
            legacy_config = self.app.legacy_config
            self.scheduler.set_context(
                'config',
                {
                    'plugins': legacy_config.plugins,
                    'temboard': legacy_config.temboard,
                    'repository': legacy_config.repository,
                }
            )


class TornadoService(Service):
    def setup(self):
        new_worker_pool(12)
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
            logger.info(
                "Serving temboardui on https://%s:%d",
                self.app.config.temboard.address,
                self.app.config.temboard.port)
            tornado.ioloop.IOLoop.instance().start()


def define_arguments(parser):
    define_core_arguments(parser, appversion=__version__)
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


class TemboardApplication(BaseApplication):
    DEFAULT_CONFIGFILE = '/etc/temboard/temboard.conf'
    DEFAULT_PLUGINS = [
        'activity',
        'dashboard',
        'monitoring',
        'pgconf',
    ]
    PROGRAM = 'temboard'
    REPORT_URL = "https://github.com/dalibo/temboard/issues"
    VERSION = __version__

    def main(self, argv, environ):

        # C O N F I G U R A T I O N

        parser = ArgumentParser(
            prog='temboard',
            description="temBoard web UI.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_arguments(parser)
        args = parser.parse_args(argv)
        self.bootstrap(args=args, environ=environ)
        # Manage logging_debug default until we use toolkit OptionSpec.
        config = legacy_bootstrap(self.config)
        self.legacy_config = config

        services = ServicesManager()

        # T A S K   M A N A G E R

        task_queue = taskmanager.Queue()
        event_queue = taskmanager.Queue()

        self.worker_pool = taskmanager.WorkerPoolService(
            app=self, name=u'worker pool',
            task_queue=task_queue, event_queue=event_queue,
        )
        self.worker_pool.apply_config()
        services.add(self.worker_pool)

        self.scheduler = SchedulerService(
            app=self, name=u'scheduler',
            task_queue=task_queue, event_queue=event_queue,
        )
        self.scheduler.apply_config()
        services.add(self.scheduler)

        # H T T P   S E R V E R

        self.webapp = make_tornado_app(config, debug=self.config.logging.debug)
        self.webapp.temboard_app = self
        webservice = TornadoService(app=self, name=u'main', services=services)

        with services:
            webservice.run()


main = TemboardApplication(specs=list_options_specs(), with_plugins=None)


if __name__ == "__main__":
    sys.exit(main())
