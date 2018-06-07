# coding: utf-8

import logging

try:
    from pkg_resources import (
        _initialize_master_working_set as refresh_distributions
    )
except ImportError:
    def refresh_distributions():
        logger.warn("setuptools is too old. Can't reload installed packages.")
        logger.warn("Restart temboard-agent if you it can't find new plugins.")

from .postgres import Postgres
from .toolkit.app import BaseApplication
from .toolkit.app import define_core_arguments as define_toolkit_arguments
from .toolkit.configuration import OptionSpec
from .toolkit import validators as v
from .version import __version__

logger = logging.getLogger(__name__)


def define_core_arguments(parser):
    define_toolkit_arguments(parser)
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=__version__
    )


class Application(BaseApplication):
    # Agent specialisation of application.
    #
    # This include some defaults and Postgres connection throught spc.

    PROGRAM = "temboard-agent"
    VERSION = __version__
    REPORT_URL = "https://github.com/dalibo/temboard-agent"

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
