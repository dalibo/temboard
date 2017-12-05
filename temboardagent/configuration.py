import logging
try:
    from logging.config import dictConfig
except ImportError:  # pragma: nocover
    from logutils.dictconfig import dictConfig

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os.path

from temboardagent.errors import ConfigurationError
from .utils import DotDict
from .pluginsmgmt import load_plugins_configurations
from .log import generate_logging_config
from .errors import UserError
from . import validators


logger = logging.getLogger(__name__)


def setup_logging(**kw):
    logging_config = generate_logging_config(**kw)
    dictConfig(logging_config)


class PluginConfiguration(configparser.RawConfigParser):
    """
    Customized configuration parser for plugins.
    """
    def __init__(self, configfile, *args, **kwargs):
        configparser.RawConfigParser.__init__(self, *args, **kwargs)
        self.configfile = configfile
        self.confdir = os.path.dirname(self.configfile)

        try:
            with open(self.configfile) as fd:
                self.readfp(fd)
        except IOError:
            raise ConfigurationError("Configuration file %s can't be opened."
                                     % (self.configfile))
        except configparser.MissingSectionHeaderError:
            raise ConfigurationError("Configuration file does not contain "
                                     "section headers.")

    def check_section(self, section):
        if not self.has_section(section):
            raise ConfigurationError("Section '%s' not found in configuration "
                                     "file %s" % (section, self.configfile))

    def abspath(self, path):
        if path.startswith('/'):
            return path
        else:
            return os.path.realpath('/'.join([self.confdir, path]))

    def getfile(self, section, name):
        path = self.abspath(self.get(section, name))
        try:
            with open(path) as fd:
                fd.read()
        except Exception as e:
            logger.warn("Failed to open %s: %s", path, e)
            raise ConfigurationError("%s file can't be opened." % (path,))
        return path


# Here begin the new API
#
# The purpose of the new API is to merge args, file, environment and defaults
# safely, even when reloading.
#
# The API must be very simple, IoC-free. Implementation must be highly testable
# and tested.


class OptionSpec(object):
    REQUIRED = object()

    # Hold known name and default of an option.
    #
    # An option *must* be specified to follow the principle of *validated your
    # inputs*.
    #
    # Defining defaults here is agnostic from origin : argparse, environ,
    # ConfigParser, etc. The origin of configuration must not take care of
    # default nor validation.
    #
    # Set default to OptionSpec.REQUIRED to enforce user definition of option
    # value.
    #
    # Option value can be None, meaning it is undefined.

    def __init__(self, section, name, validator=None, default=None):
        self.section = section
        self.name = name
        self.default = default
        self.validator = validator

    def __repr__(self):
        return '<OptionSpec %s>' % (self,)

    def __str__(self):
        return '%s_%s' % (self.section, self.name)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    @property
    def required(self):
        return self.default is self.REQUIRED

    def validate(self, value):
        if value.value is None:
            return value.value

        if not self.validator:
            return value.value

        try:
            return self.validator(value.value)
        except ValueError as e:
            logger.debug(
                "Invalid %s from %s: %.32s...", value.name, value.origin, e)
            raise


def load_configuration(specs=None, args=None, environ=os.environ):
    # Main entry point to load configuration.
    #
    # specs is a list or a flat dict of OptionSpecs
    #
    # argparser should **not** manage defaults. Use argparse.SUPPRESS as
    # argument_default to store only user defined arguments. MergeConfiguration
    # merge defaults after file and environ are loaded. Defaults from argparse
    # are considered user input and overrides file and environ.
    #
    # configfile **must** be store in dest `temboard_configfile` in args.
    #
    # Origin order: args > environ > file > defaults

    config = MergedConfiguration(specs)
    config.load(args=args, environ=environ)
    return config


class Value(object):
    # Hold an option value and its origin
    def __init__(self, name, value, origin):
        self.name = name
        self.value = value
        self.origin = origin

    def __repr__(self):
        return '<%(name)s=%(value)r %(origin)s>' % self.__dict__


def iter_args_values(args):
    # Walk args from argparse and yield values.
    if not args:
        return

    for k, v in args.__dict__.items():
        yield Value(k, v, 'args')


def iter_configparser_values(parser, filename='config'):
    for section in parser.sections():
        for name, value in parser.items(section):
            name = '%s_%s' % (section, name)
            yield Value(name, value, origin=filename)


def iter_environ_values(environ):
    prefix = 'TEMBOARD_'
    for k, v in environ.items():
        if not k.startswith(prefix):
            continue

        k = k.lower()
        v = v.decode('utf-8')

        # Yield the value with temboard prefix so we don't have to define
        # TEMBOARD_TEMBOARD_* to set a value in temboard section.
        yield Value(k, v, 'environ')
        yield Value(k[len(prefix):], v, 'environ')


def iter_defaults(specs):
    # Walk specs flat dict and yield default values.
    for spec in specs.values():
        yield Value(str(spec), spec.default, 'defaults')


class MergedConfiguration(DotDict):
    # Merge and holds configuration from args, files and more
    #
    # Origin order: args > environ > file > defaults

    def __init__(self, specs=None):
        # Spec is a flat dict of OptionSpec.
        specs = specs or {}
        if not isinstance(specs, dict):
            specs = dict((s, s) for s in specs)

        # Add required configfile option
        spec = OptionSpec(
            'temboard', 'configfile',
            default='/etc/temboard-agent/temboard-agent.conf',
            validator=validators.file_,
        )
        specs.setdefault(spec, spec)

        DotDict.__init__(self)
        self.__dict__['specs'] = specs
        self.__dict__['unvalidated_specs'] = specs.keys()
        self.loaded = False

    def add_values(self, values):
        # Search missing values in values and validate them.

        values = dict((v.name, v) for v in values)
        for name in self.unvalidated_specs[:]:
            try:
                value = values[name]
            except KeyError:
                continue

            spec = self.specs[name]
            value = spec.validate(value)
            section = self.setdefault(spec.section, {})
            section[spec.name] = value
            self.unvalidated_specs.remove(name)

    def check_required(self):
        for name in self.unvalidated_specs:
            spec = self.specs[name]
            if spec.required:
                msg = "Missing %s:%s configuration" % (spec.section, spec.name)
                raise ConfigurationError(msg)

    def load(self, args, environ):
        # Origins are loaded in order. First wins..
        #
        # Loading in this order avoid validating ignored values.

        try:
            self.add_values(iter_args_values(args))
            self.add_values(iter_environ_values(environ))
            # Loading default for configfile *before* loading file.
            spec = self.specs['temboard_configfile']
            self.add_values([Value(str(spec), spec.default, 'default')])
            self.load_file(self.temboard.configfile)
        except ValueError as e:
            raise UserError(str(e))

        self.check_required()
        self.add_values(iter_defaults(self.specs))
        self.plugins = load_plugins_configurations(self)
        self.loaded = True

    def load_file(self, filename):
        parser = configparser.RawConfigParser()
        logger.info('Reading %s.', filename)
        try:
            with open(filename, 'ro') as fp:
                parser.readfp(fp)
        except IOError as e:
            raise ValueError(str(e))

        oldpwd = os.getcwd()
        os.chdir(os.path.dirname(filename))
        self.add_values(iter_configparser_values(parser, filename))
        try:
            os.chdir(oldpwd)
        except OSError as e:
            logger.debug("Can't move back to %s: %s", oldpwd, e)

        # Compat with legacy
        self.configfile = self.temboard.configfile

    def reload(self):
        # Reread file config.

        assert self.loaded, "Can't reload unloaded configuration."
        old_plugins = self.temboard.plugins

        try:
            self.load_file(self.temboard.configfile)
        except Exception as e:
            raise ConfigurationError(str(e))

        # Prevent any change on plugins list.
        self.temboard.plugins = old_plugins
        # Now reload plugins configurations
        self.plugins = load_plugins_configurations(self)
        return self

    def setup_logging(self):
        # Just to save one import for code reloading config.
        setup_logging(**self.logging)
