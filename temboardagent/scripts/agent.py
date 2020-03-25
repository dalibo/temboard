# coding: utf-8

from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
from socket import getfqdn
import logging
import os
import datetime
import getpass

from ..toolkit import taskmanager

from ..cli import Application
from ..toolkit.configuration import OptionSpec
from ..daemon import daemonize
from ..httpd import HTTPDService
from ..routing import Router
from ..toolkit import validators as v
from ..toolkit.app import define_core_arguments
from ..toolkit.proctitle import ProcTitleManager
from ..toolkit.services import ServicesManager
from ..toolkit.tasklist.sqlite3_engine import TaskListSQLite3Engine
from ..notification import NotificationMgmt

logger = logging.getLogger('temboardagent.scripts.agent')


def define_arguments(parser):
    define_core_arguments(parser, appversion=Application.VERSION)
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


def list_options_specs():
    # Generate each option specs.
    section = 'temboard'
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
    yield OptionSpec(section, 'key')
    yield OptionSpec(
        section, 'users',
        default='/etc/temboard-agent/users', validator=v.file_,
    )
    yield OptionSpec(section, 'hostname', default=getfqdn())
    home = os.environ.get('HOME', '/var/lib/temboard-agent')
    yield OptionSpec(section, 'home', default=home, validator=v.writeabledir)


class AgentApplication(Application):
    PROGRAM = "temboard-agent"

    def bootstrap_plugins(self):
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, 'bootstrap'):
                logger.debug("Boostraping plugin %s", plugin_name)
                plugin.bootstrap()

    def main(self, argv, environ):
        parser = ArgumentParser(
            prog='temboard-agent',
            description="temBoard agent.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_arguments(parser)
        args = parser.parse_args(argv)

        setproctitle = ProcTitleManager(prefix='temboard-agent: ')
        setproctitle.setup()

        self.router = Router()

        task_queue = taskmanager.Queue()
        event_queue = taskmanager.Queue()

        self.worker_pool = taskmanager.WorkerPoolService(
            app=self, setproctitle=setproctitle, name=u'worker pool',
            task_queue=task_queue, event_queue=event_queue)
        self.services.append(self.worker_pool)

        self.scheduler = taskmanager.SchedulerService(
            app=self, setproctitle=setproctitle, name=u'scheduler',
            task_queue=task_queue, event_queue=event_queue)
        self.services.append(self.scheduler)

        self.bootstrap(args=args, environ=environ)
        config = self.config

        # TaskList engine setup must be done before we load the plugins
        self.scheduler.task_list_engine = TaskListSQLite3Engine(
            os.path.join(config.temboard['home'], 'agent_tasks.db')
        )

        self.apply_config()

        if config.postgresql.instance:
            setproctitle.prefix += config.postgresql.instance + ': '

        # Run temboard-agent as a background daemon.
        if (config.temboard.daemonize):
            daemonize(config.temboard.pidfile)

        logger.info("Starting main process.")

        self.start_datetime = datetime.datetime.now()
        self.reload_datetime = None
        self.pid = os.getpid()
        self.user = getpass.getuser()

        # Bootstraping plugins
        self.bootstrap_plugins()
        # Boostraping action logs table
        NotificationMgmt.bootstrap(config)

        # Purge all legacy data queues
        home = config.temboard['home']
        if os.path.exists(home):
            [os.remove(os.path.join(home, f))
             for f in os.listdir(home) if f.endswith('.q')]

        services = ServicesManager()
        services.add(self.worker_pool)
        services.add(self.scheduler)

        with services:
            httpd = HTTPDService(
                self, setproctitle=setproctitle, name=u'main process',
                services=services)
            httpd.run()

        return 0

    def reload(self):
        super(AgentApplication, self).reload()
        self.reload_datetime = datetime.datetime.now()


main = AgentApplication(specs=list_options_specs())

if __name__ == '__main__':  # pragma: no cover
    main()
