# coding: utf-8

import bdb
import pkg_resources
from distutils.util import strtobool
from glob import glob
import logging
import os
import pdb
from codecs import open
from site import main as refresh_pythonpath
import sys
from argparse import (
    ArgumentParser,
    Action as ArgAction,
    SUPPRESS as SUPPRESS_ARG,
)

try:
    from pkg_resources import (
        _initialize_master_working_set as refresh_distributions
    )
except ImportError:  # pragma: nocover
    def refresh_distributions():
        logger.info("setuptools is too old for plugin hotload.")
        logger.info("If new plugin can't be found, just restart.")

from .configuration import MergedConfiguration, OptionSpec
from .log import setup_logging, LastnameFilter
from .errors import UserError
from . import validators as v
from .pycompat import configparser


logger = logging.getLogger(__name__)


class StoreDefinedAction(ArgAction):
    def __call__(self, parser, namespace, values, option_string=None):
        # Store True if argument is defined.
        if values is None:
            values = True
        setattr(namespace, self.dest, values)


class BaseApplication(object):
    # This object contains application context and logic.
    #
    # The core logic is managing configuration and plugins, this is the
    # bootstrap process. Once the app is ready, it owns objects representing
    # the state of the app : config, plugins, etc. Each script or plugin can
    # add an object, it will be shared with other.

    PROGRAM = "temboard"
    VERSION = "unknown"
    REPORT_URL = "https://github.com/dalibo/temboard-agent/issues"

    DEFAULT_CONFIGFILES = [
        '%s.conf' % (LastnameFilter.root),
        '/etc/%s/%s.conf' % (LastnameFilter.root, LastnameFilter.root),
    ]
    DEFAULT_PLUGINS_EP = LastnameFilter.root + '.plugins'
    DEFAULT_PLUGINS = []

    def __init__(self, specs=None, with_plugins=DEFAULT_PLUGINS_EP, main=None):
        # If `None`, plugin loading is disabled.
        self.with_plugins = with_plugins
        self.plugins = {}
        self.config = MergedConfiguration()
        # This dict stores env, args and parser for hot reloading of
        # configuration.
        self.config_sources = dict()
        self.config_specs = self.init_specs(specs)
        # Active options specs for multi-stage parsing.
        self.active_config_specs = []
        self.services = []
        self._main = main

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__)

    def bootstrap(self, args, environ):
        # bootstrapping the app is a complex process to manage options loading
        # incrementally.

        config = self.config
        # Stage 1: Read configfile option
        config.add_specs(self.list_stage1_specs())
        self.config_sources.update(dict(args=args, environ=environ))
        config.load(**self.config_sources)

        # Stage 2: Now read configfile
        parser = configparser.RawConfigParser()
        configfile = self.find_config_file()
        if configfile is None:
            logger.info("No config file found.")
        else:
            self.config.temboard['configfile'] = configfile
            self.read_file(parser, configfile)
            self.read_dir(parser, configfile + '.d')
            self.config_sources.update(dict(
                parser=parser, pwd=os.path.dirname(configfile),
            ))

        # Stage 3: Add core and app specific options and load them.
        config.add_specs(self.config_specs.values())
        config.load(**self.config_sources)

        return self.config

    def init_specs(self, app_specs):
        # Declare all option specs.

        specs = dict()

        def add_specs(*new_specs):
            for spec in new_specs:
                specs[str(spec)] = spec

        s = 'temboard'
        add_specs(OptionSpec(
            s, 'configfile',
            validator=v.file_,
        ))
        if self.with_plugins:
            add_specs(OptionSpec(
                s, 'plugins', default=self.DEFAULT_PLUGINS,
                validator=v.jsonlist,
            ))

        s = 'logging'
        add_specs(
            OptionSpec(s, 'debug', default=False),
            OptionSpec(s, 'method', default='stderr', validator=v.logmethod),
            OptionSpec(s, 'level', default='INFO', validator=v.loglevel),
            OptionSpec(
                s, 'facility', default='local0', validator=v.syslogfacility),
            OptionSpec(s, 'destination', default='/dev/log'),
        )

        if app_specs:
            add_specs(*app_specs)

        return specs

    def list_stage1_specs(self):
        # List options specs required for bootstrap from args and environ:
        # configfile.
        return [self.config_specs[name] for name in [
            'temboard_configfile',
            # Allow to enable debug as soon as possible. Other options will
            # keep defaults.
            'logging_debug',
        ]]

    def create_parser(self, *a, **kw):
        kw.setdefault('argument_default', SUPPRESS_ARG)
        kw.setdefault('description', self.__class__.__doc__)
        kw.setdefault('prog', self.PROGRAM)
        return ArgumentParser(*a, **kw)

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

    def find_config_file(self):
        configfile = self.config.temboard.configfile
        if configfile is None:
            for configfile in self.DEFAULT_CONFIGFILES:
                configfile = os.path.abspath(configfile)
                if os.path.exists(configfile):
                    logger.info("Found config file %s.", configfile)
                    break
            else:
                configfile = None
        return configfile

    def read_file(self, parser, filename):
        logger.debug('Reading %s.', filename)
        try:
            with open(filename, 'r', 'utf-8') as fp:
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
        logger.warning("Reloading configuration.")

        # Reset file parser and load values.
        self.config_sources['parser'] = parser = configparser.RawConfigParser()
        self.read_file(parser, self.config.temboard.configfile)
        self.read_dir(parser, self.config.temboard.configfile + '.d')
        self.config.load(reload_=True, **self.config_sources)

        self.apply_config()
        logger.info("Configuration reloaded.")
        return self

    def setup_logging(self):
        setup_logging(
            systemd='SYSTEMD' in os.environ,
            **self.config.logging)

    def __call__(self, argv=sys.argv[1:], environ=os.environ):
        return self.entrypoint(argv, environ)

    def entrypoint(self, argv, environ):
        self.debug = detect_debug_mode(environ)

        retcode = 1
        try:
            setup_logging(debug=self.debug)
            logger.info("Starting %s %s.", self.PROGRAM, self.VERSION)
            retcode = self.main(argv, environ)
        except KeyboardInterrupt:
            logger.info('Terminated.')
        except bdb.BdbQuit:
            logger.info("Graceful exit from debugger.")
        except UserError as e:
            retcode = e.retcode
            logger.critical("%s", e)
        except Exception:
            logger.exception('Unhandled error:')
            if self.debug:
                pdb.post_mortem(sys.exc_info()[2])
            else:
                logger.error(
                    "%s version is %s.", LastnameFilter.root, self.VERSION)
                logger.error("This is a bug!")
                logger.error(
                    "Please report traceback to %s! Thanks!",
                    self.REPORT_URL,
                )
        exit(retcode)

    def main(self, argv, environ):
        if self._main is None:
            raise NotImplementedError()
        else:
            return self._main(self, argv, environ)


def detect_debug_mode(environ):
    debug = environ.get('DEBUG', '0')
    try:
        debug = bool(strtobool(debug))
        if debug:
            environ['TEMBOARD_LOGGING_DEBUG'] = '__debug__'
    except ValueError:
        environ['TEMBOARD_LOGGING_DEBUG'] = str(debug)
    return debug


def define_core_arguments(parser, appversion=None):
    if appversion:
        parser.add_argument(
            '-V', '--version',
            action='version',
            version=appversion,
        )
    parser.add_argument(
        '-c', '--config',
        action='store', dest='temboard_configfile',
        help="Configuration file", metavar='CONFIGFILE',
    )
    parser.add_argument(
        '--debug',
        action=StoreDefinedAction, dest='logging_debug', nargs='?',
        metavar='LOGGER,LOGGER,...',
        help=(
            "Shows debug messages for these loggers. "
            "If no loggers defined, debug all core loggers."),
    )
