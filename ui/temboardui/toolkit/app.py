import bdb
import configparser
import logging
import os
import pdb
import sys
from argparse import SUPPRESS as SUPPRESS_ARG
from argparse import Action as ArgAction
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from codecs import open
from glob import glob
from textwrap import dedent

import pkg_resources

from . import validators as v
from .configuration import MergedConfiguration, OptionSpec
from .errors import UserError
from .log import LastnameFilter, setup_logging
from .utils import strtobool

logger = logging.getLogger(__name__)


class StoreDefinedAction(ArgAction):
    def __call__(self, parser, namespace, values, option_string=None):
        # Store True if argument is defined.
        if values is None:
            values = True
        setattr(namespace, self.dest, values)


class BaseApplication:
    # This object contains application context and logic.
    #
    # The core logic is managing configuration and plugins, this is the
    # bootstrap process. Once the app is ready, it owns objects representing
    # the state of the app : config, plugins, etc. Each script or plugin can
    # add an object, it will be shared with other.

    PROGRAM = "temboard"
    VERSION = "unknown"
    REPORT_URL = "https://github.com/dalibo/temboard/issues/new"

    DEFAULT_CONFIGFILES = [
        "%s.conf" % (LastnameFilter.root),
        f"/etc/{LastnameFilter.root}/{LastnameFilter.root}.conf",
    ]
    DEFAULT_PLUGINS_EP = LastnameFilter.root + ".plugins"
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
        self.commands = {}

    def __repr__(self):
        return "<%s>" % (self.__class__.__name__)

    def bootstrap(self, args, environ, service=False):
        # bootstrapping the app is a complex process to manage options loading
        # incrementally.

        # Whether we are oneshot CLI or long running service.
        self.is_service = service
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
            logger.info("Using config file %s.", configfile)
            self.config.temboard["configfile"] = configfile
            self.read_file(parser, configfile)
            self.read_dir(parser, configfile + ".d")
            pwd = os.path.dirname(configfile)
            if pwd.endswith(".config"):
                pwd = os.path.dirname(pwd)
            self.config_sources.update(dict(parser=parser, pwd=pwd))

        # Stage 3: Add core and app specific options and load them.
        config.add_specs(self.config_specs.values())
        config.load(**self.config_sources)

        # Save loaded file.
        self.config["temboard"]["configfile"] = configfile

        return self.config

    def init_specs(self, app_specs):
        # Declare all option specs.

        specs = dict()

        def add_specs(*new_specs):
            for spec in new_specs:
                specs[str(spec)] = spec

        s = "temboard"
        add_specs(OptionSpec(s, "configfile", validator=v.file_))
        if self.with_plugins:
            add_specs(
                OptionSpec(
                    s, "plugins", default=self.DEFAULT_PLUGINS, validator=v.jsonlist
                )
            )

        s = "logging"
        add_specs(
            OptionSpec(s, "debug", default=False),
            OptionSpec(s, "method", default="stderr", validator=v.logmethod),
            OptionSpec(s, "level", default="INFO", validator=v.loglevel),
            OptionSpec(s, "facility", default="local0", validator=v.syslogfacility),
            OptionSpec(s, "destination", default="/dev/log"),
        )

        if app_specs:
            add_specs(*app_specs)

        return specs

    def list_stage1_specs(self):
        # List options specs required for bootstrap from args and environ:
        # configfile.
        return [
            self.config_specs[name]
            for name in [
                "temboard_configfile",
                # Allow to enable debug as soon as possible. Other options will
                # keep defaults.
                "logging_debug",
            ]
        ]

    def create_parser(self, *a, **kw):
        kw.setdefault("argument_default", SUPPRESS_ARG)
        _, d = extract_help_description_from_docstring(self.__class__.__doc__)
        kw.setdefault("description", d)
        kw.setdefault("prog", self.PROGRAM)
        kw.setdefault("formatter_class", RawDescriptionHelpFormatter)
        return ArgumentParser(*a, **kw)

    def command(self, cls):
        # Class-decorator to instanciate and register a subcommand.
        command = cls.singleton = cls(self)
        self.commands[command.fullname] = command
        return cls

    def define_arguments(self, parser):
        # Configure an argparse parser for each subcommands declared with
        # @self.command class decorator.

        if not self.commands:
            return

        subparsers = parser.add_subparsers(
            title="Available commands",
            metavar="COMMAND",
            help="Name of one sub-command described bellow.",
        )

        for fullname, command in self.commands.items():
            if "." in fullname:
                continue  # Let commands declare their sub-commands.

            h, d = extract_help_description_from_docstring(command.__doc__)
            subparser = subparsers.add_parser(
                command.name,
                help=h,
                description=d,
                formatter_class=parser.formatter_class,
                argument_default=parser.argument_default,
            )
            subparser.set_defaults(command_fullname=fullname)
            command.define_arguments(subparser)

    def apply_config(self):
        # Once config is loaded or reloaded, update application state to match
        # new configuration.

        try:
            self.setup_logging()
        except Exception as e:
            raise UserError(f"Failed to setup logging: {e}.")
        for service in self.services:
            service.apply_config()

        if not self.with_plugins:
            return

        plugins = self.create_plugins()
        if plugins:
            logger.debug("Reading plugins configuration.")
            self.config.load(**self.config_sources)
        self.load_plugins(plugins)

    def find_config_file(self):
        configfile = self.config.temboard.configfile
        if configfile is None:
            for configfile in self.DEFAULT_CONFIGFILES:
                configfile = os.path.abspath(configfile)
                logger.debug("trying %s.", configfile)
                if os.path.exists(configfile):
                    break
            else:
                configfile = None
        return configfile

    def read_file(self, parser, filename):
        logger.debug("Reading %s.", filename)
        try:
            with open(filename, "r", "utf-8") as fp:
                parser.read_file(fp)
        except OSError as e:
            raise UserError(str(e))

    def read_dir(self, parser, dirname):
        if not os.path.isdir(dirname):
            return
        for filename in sorted(glob(dirname + "/*.conf")):
            self.read_file(parser, filename)

    def fetch_plugin(self, name):
        logger.debug("Looking for plugin %s.", name)
        for ep in pkg_resources.iter_entry_points(self.with_plugins, name):
            logger.debug("Found plugin %s.", ep)
            try:
                return ep.load()
            except Exception:
                logger.exception("Error while loading %s.", ep)
                raise UserError(f"Failed to load {ep.name}.")
        else:
            raise UserError(f"Missing plugin: {name}.")

    def create_plugins(self):
        self.config.plugins = dict()

        # Filter legacy plugins
        ng_plugins = filter(
            lambda name: name not in self.config.plugins, self.config.temboard.plugins
        )
        # Filter already loaded plugins
        unloaded_names = [n for n in ng_plugins if n not in self.plugins]

        for name in unloaded_names:
            cls = self.fetch_plugin(name)
            plugin = cls(self)
            self.plugins[name] = plugin
            self.config.plugins.pop(name, None)

        return unloaded_names

    def load_plugins(self, plugins):
        for name in plugins:
            logger.debug("Loading plugin %s.", name)
            self.plugins[name].load()

    def reload(self):
        logger.info("Reloading configuration.")

        # Reset file parser and load values.
        self.config_sources["parser"] = parser = configparser.RawConfigParser()
        configfile = self.config.temboard.configfile
        self.read_file(parser, configfile)
        self.read_dir(parser, configfile + ".d")
        self.config.load(reload_=True, **self.config_sources)
        self.config["temboard"]["configfile"] = configfile

        self.apply_config()
        logger.debug("Configuration reloaded.")
        return self

    def setup_logging(self):
        if self.config.logging.method != "stderr" and not self.is_service:
            # Enforce stderr method for one shot command, this avoid creating a
            # logfile with bad privileges, and spam syslog or logfile with
            # command logs.
            logger.debug(
                "Disabling log method %s for one shot command.",
                self.config.logging.method,
            )
            self.config.logging.method = "stderr"

        setup_logging(systemd="SYSTEMD" in os.environ, **self.config.logging)

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
            logger.info("Interrupted.")
        except bdb.BdbQuit:
            logger.info("Graceful exit from debugger.")
        except UserError as e:
            retcode = e.retcode
            logger.critical("%s", e)
        except Exception:
            logger.exception("Unhandled error:")
            if self.debug:
                pdb.post_mortem(sys.exc_info()[2])
            else:
                logger.error("%s version is %s.", LastnameFilter.root, self.VERSION)
                logger.error("This is a bug!")
                logger.error("Please report traceback to %s! Thanks!", self.REPORT_URL)
        exit(retcode)

    def main(self, argv, environ):
        if self._main is None:
            raise NotImplementedError()
        else:
            return self._main(self, argv, environ)


class SubCommand:
    # Base class for sub-command.
    #
    # Almost everything keeps in app object. Sub commands is roughly a set of
    # two fuctions : one to define argparse arguments, the other is the main
    # code to execute after app initialization.
    #
    # Class docstring is injected in argparse help for the command.

    name = None
    # Whether oneshot CLI or long running service. This is handled by
    # Application.setup_logging.
    is_service = False

    def __init__(self, parent):
        self.parent = parent  # The app or another command.

        names = []
        root = self.parent
        while hasattr(root, "parent"):
            names[0:] = [root.name]
            root = root.parent

        if names:
            names.append("")  # Add final .

        if not self.name:
            self.name = self.__class__.__name__.lower()
        self.app = root
        self.prefix = ".".join(names)
        self.fullname = self.prefix + self.name

    def __repr__(self):
        return "<%s>" % (self.__class__.__name__)

    @classmethod
    def command(cls, subcommand_cls):
        # Class decorator to instanciate and register a subcommand.
        self = cls.singleton
        command = subcommand_cls.singleton = subcommand_cls(self)
        self.app.commands[command.fullname] = command
        return subcommand_cls

    @property
    def commands(self):
        app = self.app
        prefix = self.fullname + "."
        my_commands = {}
        for fullname, command in app.commands.items():
            if not fullname.startswith(prefix):
                continue
            my_commands[fullname] = command

        return my_commands

    def define_arguments(self, parser):
        # Configure an argparse parser for each subcommands declared with
        # @self.command class decorator.

        my_commands = self.commands
        if not my_commands:
            return

        subparsers = parser.add_subparsers(
            title="Available commands",
            metavar="COMMAND",
            help="Name of one sub-command described bellow.",
        )

        for fullname, command in my_commands.items():
            subparser = subparsers.add_parser(command.name, help=command.__doc__)
            subparser.set_defaults(command_fullname=fullname)
            command.define_arguments(subparser)

    def main(self, args):
        raise NotImplementedError()


def detect_debug_mode(environ):
    debug = environ.get("DEBUG", "0")
    try:
        debug = bool(strtobool(debug))
        if debug:
            environ["TEMBOARD_LOGGING_DEBUG"] = "__debug__"
    except ValueError:
        environ["TEMBOARD_LOGGING_DEBUG"] = str(debug)
    return debug


def define_core_arguments(parser, appversion=None):
    if appversion:
        parser.add_argument("-V", "--version", action="version", version=appversion)
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        dest="temboard_configfile",
        help="Configuration file",
        metavar="CONFIGFILE",
    )
    parser.add_argument(
        "--verbose",
        "--debug",
        action="store_const",
        const="temboardui",
        dest="logging_debug",
        help="Enable verbose messages for temBoard.",
    )


def extract_help_description_from_docstring(docstring):
    docstring = docstring or ""

    if "\n " in docstring:
        title, description = docstring.split("\n", 1)
        description = f"{title}\n{dedent(description)}"
    else:
        title = description = docstring

    return title, description
