import logging
import sys
from platform import python_version

from .postgres import Postgres
from .toolkit.app import BaseApplication
from .toolkit.configuration import OptionSpec
from .toolkit import validators as v
from .version import __version__


logger = logging.getLogger(__name__)


class Application(BaseApplication):
    # Agent specialisation of application.
    #
    # This include some defaults and Postgres connection.

    PROGRAM = "temboard-agent"
    VERSION = __version__
    REPORT_URL = "https://github.com/dalibo/temboard-agent"

    DEFAULT_CONFIGFILES = [
        '/etc/temboard-agent/temboard-agent.conf',
        'temboard-agent.conf',
    ]
    DEFAULT_PLUGINS = [
        "activity",
        "administration",
        "dashboard",
        "monitoring",
        "pgconf",
        "maintenance",
        "statements",
    ]

    def init_specs(self, app_specs):
        specs = super().init_specs(app_specs)

        def add_specs(*new_specs):
            for spec in new_specs:
                specs[str(spec)] = spec

        # These are *core* because they are needed to load plugins.
        s = 'postgresql'
        add_specs(
            OptionSpec(
                s, 'host', default='/var/run/postgresql', validator=v.dir_),
            OptionSpec(s, 'instance', default='main'),
            OptionSpec(s, 'port', default=5432, validator=v.port),
            OptionSpec(s, 'user', default='postgres'),
            OptionSpec(s, 'password'),
            OptionSpec(s, 'dbname', default='postgres'),
        )

        return specs

    def core_specs(self):
        for spec in super().core_specs():
            yield spec

        for name, spec in self.config_specs.items():
            if name.startswith('postgresql_'):
                yield spec

    def apply_config(self):
        self.postgres = Postgres(app=self, **self.config.postgresql)
        return super().apply_config()

    def check_compatibility(self, pg_version):
        # check for compatibility with plugins
        for name, plugin in self.plugins.items():
            if pg_version < plugin.PG_MIN_VERSION[0]:
                logger.error(
                    "%s plugin is incompatible with Postgres below %s",
                    name, plugin.PG_MIN_VERSION[1],
                )

    def log_versions(self):
        versions = inspect_versions()
        logger.info(
            "Running on %s %s.",
            versions['distname'], versions['distversion'])
        logger.info(
            "Using Python %s (%s).",
            versions['python'], versions['pythonbin'])
        logger.info(
            "Using libpq %s, Psycopg2 %s.",
            versions['libpq'], versions['psycopg2'],
        )


def inspect_versions():
    from .toolkit.versions import (
        format_pq_version,
        read_distinfo,
        read_libpq_version,
    )
    from psycopg2 import __version__ as psycopg2_version

    distinfos = read_distinfo()

    return dict(
        distname=distinfos['NAME'],
        distversion=distinfos['VERSION'],
        libpq=format_pq_version(read_libpq_version()),
        psycopg2=psycopg2_version,
        python=python_version(),
        pythonbin=sys.executable,
        temboard=__version__,
    )
