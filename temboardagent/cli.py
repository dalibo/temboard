# coding: utf-8

from argparse import Action as ArgAction
import pkg_resources
from distutils.util import strtobool
from glob import glob
import logging
import os
import pdb
from site import main as refresh_pythonpath
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    from pkg_resources import (
        _initialize_master_working_set as refresh_distributions
    )
except ImportError:
    def refresh_distributions():
        logger.warn("setuptools is too old. Can't reload installed packages.")
        logger.warn("Restart temboard-agent if you it can't find new plugins.")

from .postgres import Postgres
from .toolkit.configuration import MergedConfiguration, OptionSpec
from .toolkit.log import setup_logging, LastnameFilter
from .toolkit.errors import UserError
from .toolkit import validators as v
from .version import __version__

logger = logging.getLogger(__name__)


class StoreDefinedAction(ArgAction):
    def __call__(self, parser, namespace, values, option_string=None):
        # Store True if argument is defined.
        if values is None:
            values = True
        setattr(namespace, self.dest, values)


def define_core_arguments(parser):
    parser.add_argument(
        '-c', '--config',
        action='store', dest='temboard_configfile',
        help="Configuration file",
    )
    parser.add_argument(
        '--debug',
        action=StoreDefinedAction, dest='logging_debug', nargs='?',
        metavar='LOGGER,LOGGER,...',
        help=(
            "Shows debug messages for these loggers. "
            "If no loggers defined, debug all core loggers."),
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=__version__
    )


class BaseApplication(object):
    # This object contains application context and logic.
    #
    # The core logic is managing configuration and plugins, this is the
    # bootstrap process. Once the app is ready, it owns objects representing
    # the state of the app : config, plugins, etc. Each script or plugin can
    # add an object, it will be shared with other.

    DEFAULT_CONFIGFILE = '/etc/%s/%s.conf' % (
        LastnameFilter.root, LastnameFilter.root)
    DEFAULT_PLUGINS_EP = LastnameFilter.root + '.plugins'
    DEFAULT_PLUGINS = []

    def __init__(self, specs=None, with_plugins=DEFAULT_PLUGINS_EP):
        self.specs = list(specs) if specs else []
        # If `None`, plugin loading is disabled.
        self.with_plugins = with_plugins
        self.plugins = {}
        self.config = MergedConfiguration()
        # This dict stores env, args and parser for hot reloading of
        # configuration.
        self.config_sources = dict()
        self.services = []

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__)

    def bootstrap(self, args, environ):
        # bootstrapping the app is a complex process to manage options loading
        # incrementally.

        config = self.config
        # Stage 1: Read configfile option
        config.add_specs(self.bootstrap_specs())
        self.config_sources.update(dict(args=args, environ=environ))
        config.load(**self.config_sources)

        # Stage 2: Now read configfile
        parser = configparser.RawConfigParser()
        configfile = config.temboard.configfile
        self.read_file(parser, configfile)
        self.read_dir(parser, configfile + '.d')
        self.config_sources.update(dict(
            parser=parser, pwd=os.path.dirname(configfile)
        ))

        # Stage 3: Add core and app specific options, load them and apply.
        config.add_specs(self.core_specs())
        config.add_specs(self.specs)
        config.load(**self.config_sources)
        self.apply_config()

        return self.config

    def bootstrap_specs(self):
        # Generate options specs required for bootstrap from args and environ:
        # configfile.
        yield OptionSpec(
            'temboard', 'configfile',
            default=self.DEFAULT_CONFIGFILE,
            validator=v.file_,
        )

    def core_specs(self):
        # Generate options specs required for bootstrap from args and environ
        # and file : logging, plugins, postgresql.

        s = 'temboard'
        if self.with_plugins:
            yield OptionSpec(
                s, 'plugins', default=self.DEFAULT_PLUGINS,
                validator=v.jsonlist,
            )

        s = 'logging'
        yield OptionSpec(s, 'method', default='syslog', validator=v.logmethod)
        yield OptionSpec(s, 'level', default='INFO', validator=v.loglevel)
        yield OptionSpec(
            s, 'facility', default='local0', validator=v.syslogfacility,
        )
        yield OptionSpec(s, 'destination', default='/dev/log')
        yield OptionSpec(s, 'debug', default=False)

    def apply_config(self):
        # Once config is loaded or reloaded, update application state to match
        # new configuration.

        try:
            self.setup_logging()
        except Exception as e:
            raise UserError("Failed to setup logging: %s." % (e,))
        for service in self.services:
            service.apply_config()

        if not self.with_plugins:
            return

        old_plugins = self.purge_plugins()
        new_plugins = self.create_plugins()
        if new_plugins:
            logger.debug("Reading new plugins configuration.")
            self.config.load(**self.config_sources)
        self.update_plugins(old_plugins=old_plugins)

    def read_file(self, parser, filename):
        logger.debug('Reading %s.', filename)
        try:
            with open(filename, 'r') as fp:
                parser.readfp(fp)
        except IOError as e:
            raise UserError(str(e))

    def read_dir(self, parser, dirname):
        if not os.path.isdir(dirname):
            return
        for filename in sorted(glob(dirname + '/*.conf')):
            self.read_file(parser, filename)

    def fetch_plugin(self, name):
        logger.debug("Looking for plugin %s.", name)
        for ep in pkg_resources.iter_entry_points(self.with_plugins, name):
            logger.info("Found plugin %s.", ep)
            try:
                return ep.load()
            except Exception:
                logger.exception("Error while loading %s.", ep)
                raise UserError("Failed to load %s." % (ep.name,))
        else:
            raise UserError("Missing plugin: %s." % (name,))

    def create_plugins(self):
        self.config.plugins = dict()

        # Filter legacy plugins
        ng_plugins = filter(
            lambda name: name not in self.config.plugins,
            self.config.temboard.plugins
        )
        # Filter already loaded plugins
        unloaded_names = [
            n for n in ng_plugins
            if n not in self.plugins
        ]

        # Refresh sys.path and working_set to ensure new code is loadable.
        refresh_pythonpath()
        refresh_distributions()

        for name in unloaded_names:
            cls = self.fetch_plugin(name)
            plugin = cls(self)
            self.plugins[name] = plugin
            self.config.plugins.pop(name, None)

        return unloaded_names

    def update_plugins(self, old_plugins=None):
        # Load and unload plugins
        old_names = set(old_plugins or [])
        new_names = set(self.plugins)

        to_unload = old_names - new_names
        for name in to_unload:
            logger.info("Unloading plugin %s.", name)
            old_plugins[name].unload()

        to_load = new_names - old_names
        for name in to_load:
            logger.info("Loading plugin %s.", name)
            self.plugins[name].load()

    def purge_plugins(self):
        old_plugins = self.plugins.copy()
        for name in list(self.plugins):
            if name in self.config.temboard.plugins:
                continue
            del self.plugins[name]
        return old_plugins

    def reload(self):
        logger.warn("Reloading configuration.")

        # Reset file parser and load values.
        self.config_sources['parser'] = parser = configparser.RawConfigParser()
        self.read_file(parser, self.config.temboard.configfile)
        self.read_dir(parser, self.config.temboard.configfile + '.d')
        self.config.load(reload_=True, **self.config_sources)

        self.apply_config()
        logger.info("Configuration reloaded.")
        return self

    def setup_logging(self):
        setup_logging(**self.config.logging)


class Application(BaseApplication):
    # Agent specialisation of application.
    #
    # This include some defaults and Postgres connection throught spc.

    DEFAULT_CONFIGFILE = '/etc/temboard-agent/temboard-agent.conf'
    DEFAULT_PLUGINS = [
        "activity",
        "administration",
        "dashboard",
        "monitoring",
        "pgconf",
    ]

    def core_specs(self):
        for spec in super(Application, self).core_specs():
            yield spec

        # These are *core* because they are needed to load plugins.
        s = 'postgresql'
        yield OptionSpec(
            s, 'host', default='/var/run/postgresql', validator=v.dir_)
        yield OptionSpec(s, 'instance', default='main')
        yield OptionSpec(s, 'port', default=5432, validator=v.port)
        yield OptionSpec(s, 'user', default='postgres')
        yield OptionSpec(s, 'password')
        yield OptionSpec(s, 'dbname', default='postgres')

    def apply_config(self):
        self.postgres = Postgres(**self.config.postgresql)
        return super(Application, self).apply_config()


def bootstrap(args, environ, **kw):
    # Fastpath for simple script without extra context.
    app = Application(**kw)
    app.bootstrap(args=args, environ=environ)
    return app


def detect_debug_mode(environ):
    debug = environ.get('DEBUG', '0')
    try:
        debug = bool(strtobool(debug))
        if debug:
            environ['TEMBOARD_LOGGING_DEBUG'] = '__debug__'
    except ValueError:
        environ['TEMBOARD_LOGGING_DEBUG'] = str(debug)
    return debug


def cli(main):
    # A decorator to add consistent CLI behaviour.
    #
    # Decorated function must accept argv and environ arguments and return an
    # exit code.
    #
    # The decorator adds basic logging setup and error management. The
    # decorated function can just raise exception and log using logging module
    # as usual.

    def cli_wrapper(argv=sys.argv[1:], environ=os.environ):
        debug = detect_debug_mode(environ)

        retcode = 1
        try:
            setup_logging(debug=debug)
            logger.debug("Starting temBoard agent %s.", __version__)
            retcode = main(argv, environ) or 1
        except KeyboardInterrupt:
            logger.info('Terminated.')
        except pdb.bdb.BdbQuit:
            logger.info("Graceful exit from debugger.")
        except UserError as e:
            retcode = e.retcode
            logger.critical("%s", e)
        except Exception:
            logger.exception('Unhandled error:')
            if debug:
                pdb.post_mortem(sys.exc_info()[2])
            else:
                logger.error("temboard-agent version is %s.", __version__)
                logger.error("This is a bug!")
                logger.error(
                    "Please report traceback to "
                    "https://github.com/dalibo/temboard-agent/issues! "
                    "Thanks!"
                )
        exit(retcode)
    return cli_wrapper
