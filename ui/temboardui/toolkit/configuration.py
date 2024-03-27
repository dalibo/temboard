# The configuration API merges args, file, environment and defaults safely,
# even when reloading.

import logging
import os
from argparse import SUPPRESS as SUPPRESS_ARG

from .utils import DotDict
from .errors import UserError


logger = logging.getLogger(__name__)


class OptionSpec:
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
        return f'<OptionSpec {self}>'

    def __str__(self):
        return f'{self.section}_{self.name}'

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    @property
    def required(self):
        return self.default is self.REQUIRED

    def add_argument(self, parser, *a, **kw):
        help_ = kw.get('help')
        if help_:
            help_ = help_ % dict(
                default="*required*" if self.required else self.default,
            )
            # Escape % for Argparse formatting.
            kw['help'] = help_.replace("%", "%%")

        kw.setdefault('dest', str(self))
        kw.setdefault('default', SUPPRESS_ARG)

        return parser.add_argument(*a, **kw)

    def validate(self, value):
        if value.value is None or not self.validator:
            return value.value

        try:
            return self.validator(value.value)
        except ValueError as e:
            logger.error(
                "Invalid %s from %s: %s...", value.name, value.origin, e)
            raise


class Value:
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
            name = f'{section}_{name}'

            if value.startswith('"') and value.startswith('"'):
                raise UserError(
                    "You must not quote string in configuration (%s)."
                    % name.replace('_', '.')
                )

            if value.startswith("'") and value.startswith("'"):
                raise UserError(
                    "You must not quote string in configuration (%s)."
                    % name.replace('_', '.')
                )

            yield Value(name, value, origin=filename)


def iter_environ_values(environ):
    environ = environ or {}
    prefix = 'TEMBOARD_'
    for k, v in environ.items():
        if not k.startswith(prefix):
            continue

        k = k.lower()
        if hasattr(v, 'decode'):
            v = v.decode('utf-8')

        # Yield the value with temboard prefix so we don't have to define
        # TEMBOARD_TEMBOARD_* to set a value in temboard section.
        yield Value(k, v, 'environ')
        yield Value(k[len(prefix):], v, 'environ')


def iter_defaults(specs):
    # Walk specs flat dict and yield default values.
    for spec in specs.values():
        if spec.required:
            continue
        yield Value(str(spec), spec.default, 'defaults')


class MergedConfiguration(DotDict):
    # Merge and holds configuration from args, files and more
    #
    # Origin order: args > environ > file > defaults

    def __init__(self, specs=None):
        super().__init__()
        setattr(self, 'specs', {s: s for s in specs or []})
        setattr(self, 'unvalidated_specs', set(self.specs))

    def add_specs(self, specs):
        for s in specs:
            self.specs[s] = s
            self.unvalidated_specs.add(s)

    def remove_specs(self, specs):
        self.unvalidated_specs -= set(specs)
        for s in specs:
            self.specs.pop(s, None)
            # Clean value
            try:
                del self[s.section][s.name]
            except KeyError:
                pass

            # Clean section if empty
            if not self.get(s.section):
                self.pop(s.section, None)

    def add_values(self, values):
        # Search missing values in values and validate them.

        values = {v.name: v for v in values}
        for name in list(self.unvalidated_specs):
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
                msg = f"Missing {spec.section}:{spec.name} configuration"
                raise UserError(msg)

    def load(self, args=None, environ=None, parser=None, pwd=None,
             reload_=False):
        # Origins are loaded in order. First wins..
        #
        # Loading in this order avoid validating ignored values.

        if reload_:
            # Reset unvalidated set to re-analyze all options.
            self.unvalidated_specs.update(set(self.specs))

        try:
            self.add_values(iter_args_values(args))
            self.add_values(iter_environ_values(environ))
        except ValueError as e:
            logger.debug("Bad value %s.", e)
            raise UserError("Failed to load configuration.")

        if pwd:
            try:
                # configfile and default values are relative to configfile
                # directory.
                oldpwd = os.getcwd()
            except OSError as e:
                raise UserError("Failed to get CWD: %s" % e)

            try:
                os.chdir(pwd)
            except OSError as e:
                raise UserError(f"Failed to access {pwd}: {e}")
        else:
            oldpwd = None

        try:
            if parser:
                self.add_values(iter_configparser_values(parser))
            self.add_values(iter_defaults(self.specs))
        except ValueError as e:
            logger.debug("Bad value %s.", e)
            raise UserError("Failed to load configuration.")

        if oldpwd:
            try:
                os.chdir(oldpwd)
            except OSError as e:
                logger.warning("Can't move back to %s: %s", oldpwd, e)

        self.check_required()
