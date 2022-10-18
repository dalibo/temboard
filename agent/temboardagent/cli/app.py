import logging
import os
import datetime
import getpass
from argparse import _VersionAction
from socket import getfqdn
from textwrap import dedent

try:
    import hupper
except ImportError:
    hupper = None

from ..core import workers
from ..discover import Discover, inspect_versions
from ..queries import QUERIES
from ..status import Status
from ..toolkit.configuration import OptionSpec
from ..toolkit.errors import UserError
from ..web import HTTPDService
from ..postgres import Postgres
from ..toolkit import taskmanager, validators as v
from ..toolkit.app import BaseApplication, define_core_arguments
from ..toolkit.configuration import MergedConfiguration
from ..toolkit.proctitle import ProcTitleManager
from ..toolkit.signing import load_public_key
from ..toolkit.tasklist.sqlite3_engine import TaskListSQLite3Engine
from ..notification import NotificationMgmt
from ..version import __version__


logger = logging.getLogger('temboardagent.scripts.agent')


class TemboardAgentApplication(BaseApplication):
    PROGRAM = "temboard-agent"
    VERSION = __version__

    DEFAULT_CONFIGFILES = [
        '/etc/temboard-agent/temboard-agent.conf',
        'temboard-agent.conf',
    ]
    DEFAULT_PLUGINS = [
        "activity",
        "administration",
        "dashboard",
        "maintenance",
        "monitoring",
        "pgconf",
        "statements",
    ]

    def __init__(self, *a, **kw):
        super(TemboardAgentApplication, self).__init__(*a, **kw)
        self.config = TemboardAgentConfiguration()

    def main(self, argv, environ):
        parser = self.create_parser(
            description=dedent("""\
            temBoard agent %s.

            COMMAND is optional. Default command is `serve`, the combined
            service. See available commands below.

            """) % __version__,
        )
        self.define_arguments(parser)
        args = parser.parse_args(argv)

        command_name = getattr(args, 'command_fullname', 'serve')
        command = self.commands[command_name]

        setproctitle = ProcTitleManager(prefix='temboard-agent: ')

        task_queue = taskmanager.Queue()
        event_queue = taskmanager.Queue()

        self.worker_pool = taskmanager.WorkerPoolService(
            app=self, setproctitle=setproctitle, name='worker pool',
            task_queue=task_queue, event_queue=event_queue)
        self.services.append(self.worker_pool)
        self.worker_pool.add(workers)

        self.scheduler = taskmanager.SchedulerService(
            app=self, setproctitle=setproctitle, name='scheduler',
            task_queue=task_queue, event_queue=event_queue)
        self.services.append(self.scheduler)

        self.httpd = HTTPDService(
            self, setproctitle=setproctitle, name='web',
        )

        self.bootstrap(args=args, environ=environ, service=command.is_service)
        self.log_versions()
        config = self.config

        self.discover = Discover(self)
        self.discover.read()
        self.status = Status(self)

        # TaskList engine setup must be done before we load the plugins
        self.scheduler.task_list_engine = TaskListSQLite3Engine(
            os.path.join(config.temboard['home'], 'agent_tasks.db')
        )

        self.apply_config()

        if self.debug and hupper and command.is_service:
            self.setup_autoreload()

        setproctitle.setup()

        if '.' not in self.config.temboard.hostname:
            logger.warning(
                "Hostname %s is not a FQDN.",
                self.config.temboard.hostname
            )

        cluster_name = self.discover.data['postgres'].get('cluster_name')
        if cluster_name:
            setproctitle.prefix += cluster_name + ': '

        QUERIES.load(self.discover.data['postgres'].get('version_num'))

        self.start_datetime = datetime.datetime.now()
        self.reload_datetime = None
        self.pid = os.getpid()
        self.user = getpass.getuser()

        self.bootstrap_plugins()

        # Boostraping action logs table
        NotificationMgmt.bootstrap(config)

        return command.main(args)

    def apply_config(self):
        self.postgres = Postgres(app=self, **self.config.postgresql)
        self.postgres.connection_lost_observers.append(
            self.discover.connection_lost)
        return super().apply_config()

    def bootstrap_plugins(self):
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, 'bootstrap'):
                logger.debug("Boostraping plugin %s", plugin_name)
                plugin.bootstrap()

    def check_compatibility(self, pg_version):
        # check for compatibility with plugins
        for name, plugin in self.plugins.items():
            if pg_version < plugin.PG_MIN_VERSION[0]:
                logger.error(
                    "%s plugin is incompatible with Postgres below %s",
                    name, plugin.PG_MIN_VERSION[1],
                )

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
            help="PID file.",
        )
        super(TemboardAgentApplication, self).define_arguments(parser)

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

    def log_versions(self):
        versions = inspect_versions()
        logger.debug(
            "Running on %s %s.",
            versions['distname'], versions['distversion'])
        logger.debug(
            "Using Python %s (%s).",
            versions['python'], versions['pythonbin'])
        logger.debug(
            "Using libpq %s, Psycopg2 %s.",
            versions['libpq'], versions['psycopg2'],
        )

    def reload(self):
        super().reload()
        self.reload_datetime = datetime.datetime.now()

    def setup_autoreload(self):
        logger.debug("Enabling code autoreload using hupper.")
        reloader = hupper.start_reloader('temboardagent.__main__.main')
        reloader.watch_files(QUERIES.iter_files())
        reloader.watch_files(filter(None, [
            self.config.temboard.configfile,
            self.config.temboard.ssl_ca_cert_file,
            self.config.temboard.ssl_cert_file,
            self.config.temboard.ssl_key_file,
        ]))


class TemboardAgentConfiguration(MergedConfiguration):
    def __init__(self, *a, **kw):
        super(TemboardAgentConfiguration, self).__init__(*a, **kw)
        self._signing_key = None

    @property
    def signing_key(self):
        # Lazy load signing key.
        if not self._signing_key:
            self.load_signing_key()
        return self._signing_key

    def load_signing_key(self):
        path = self.temboard.signing_public_key
        logger.debug("Loading signing key from %s.", path)
        try:
            fo = open(path, 'rb')
        except OSError as e:
            raise UserError("Failed to load signing key: %s" % e)

        with fo:
            self._signing_key = load_public_key(fo.read())


class VersionAction(_VersionAction):
    fmt = dedent("""\
    temBoard agent %(temboard)s (%(temboardbin)s)
    System %(distname)s %(distversion)s
    Python %(python)s (%(pythonbin)s)
    bottle %(bottle)s
    cryptography %(cryptography)s
    libpq %(libpq)s
    psycopg2 %(psycopg2)s
    """)

    def __call__(self, parser, *_):
        print((self.fmt % inspect_versions()).strip())
        parser.exit()


def list_options_specs():
    # Generate each option specs.
    section = 'temboard'
    yield OptionSpec(section, 'ui_url', validator=v.url)
    yield OptionSpec(section, 'daemonize', default=False)
    yield OptionSpec(section, 'pidfile', default='/run/temboard-agent.pid')
    yield OptionSpec(
        section, 'address', default='0.0.0.0', validator=v.address)
    yield OptionSpec(section, 'port', validator=v.port, default=2345)
    yield OptionSpec(
        section, 'ssl_cert_file',
        default=OptionSpec.REQUIRED, validator=v.file_)
    yield OptionSpec(
        section, 'ssl_key_file',
        default=OptionSpec.REQUIRED, validator=v.file_)
    yield OptionSpec(section, 'ssl_ca_cert_file', validator=v.file_)
    yield OptionSpec(
        section, 'signing_public_key', default='signing-public.pem',
        validator=v.path)
    yield OptionSpec(section, 'key')
    yield OptionSpec(section, 'hostname', default=getfqdn(), validator=v.fqdn)
    home = os.environ.get('HOME', '/var/lib/temboard-agent')
    yield OptionSpec(section, 'home', default=home, validator=v.writeabledir)


app = TemboardAgentApplication(specs=list_options_specs())
