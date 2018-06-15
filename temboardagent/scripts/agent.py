# coding: utf-8

from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
from socket import getfqdn
import functools
import logging
import os
import sys
import datetime
import getpass

from ..toolkit import taskmanager

from ..cli import Application
from ..cli import define_core_arguments
from ..toolkit.configuration import OptionSpec
from ..daemon import daemonize
from ..httpd import HTTPDService
from ..routing import Router
from ..services import Service, ServicesManager
from ..queue import purge_queue_dir
from ..toolkit import validators as v
from ..toolkit.proctitle import ProcTitleManager


logger = logging.getLogger('temboardagent.scripts.agent')


class SchedulerService(Service):
    # Adapter from taskmanager.Scheduler to Service

    def __init__(self, task_queue, event_queue, **kw):
        super(SchedulerService, self).__init__(**kw)
        self.task_queue = task_queue
        self.event_queue = event_queue
        self.scheduler = None

    def apply_config(self):
        # Setup scheduler as soon as configuration is loaded, before
        # plugins, so that tasklist is created before plugins.
        if not self.scheduler:
            self.scheduler = taskmanager.Scheduler(
                address=os.path.join(
                    self.app.config.temboard.home, '.tm.socket'),
                task_path=os.path.join(
                    self.app.config.temboard.home, '.tm.task_list'),
                authkey=None)
            self.scheduler.task_queue = self.task_queue
            self.scheduler.event_queue = self.event_queue
            self.scheduler.setup_task_list()

    def setup(self):
        if os.path.exists(self.scheduler.address):
            os.unlink(self.scheduler.address)

        self.scheduler.setup()

    def serve1(self):
        self.scheduler.serve1()

    def add(self, workerset):
        if not self.is_my_process:
            return

        for task in workerset.list_tasks():
            try:
                self.scheduler.task_list.rm(task.id)
                logger.debug("Overwriting task %s.", task.id)
            except Exception:
                pass

            self.scheduler.task_list.push(task)

    def remove(self, workerset):
        if not self.is_my_process:
            return

        for task in workerset.list_tasks():
            self.scheduler.task_list.rm(task.id)


class WorkerPoolService(Service):
    # Adapter from taskmanager.WorkerPool to Service

    def __init__(self, task_queue, event_queue, **kw):
        super(WorkerPoolService, self).__init__(**kw)
        self.worker_pool = taskmanager.WorkerPool(task_queue, event_queue)

    def setup(self):
        self.worker_pool.setup()

    def serve1(self):
        try:
            self.worker_pool.serve1()
        except Exception:
            logger.exception("Unhandled error in worker:")
            logger.error("Not stopping worker process.")

    def create_task_function_app_wrapper(self, function):
        @functools.wraps(function)
        def wrapper(*a, **kw):
            return function(app=self.app, *a, **kw)
        wrapper._tm_function = function
        return wrapper

    def add(self, workerset):
        if not self.is_my_process:
            return

        for function in workerset:
            conf = function._tm_worker
            wrapper = self.create_task_function_app_wrapper(function)

            # Inject wrapper in module so taskmanager will find it.
            mod = sys.modules[conf['module']]
            wrapper_name = '_tm_wrapper_' + function.__name__
            setattr(mod, wrapper_name, wrapper)
            conf['function'] = wrapper_name

            # Add to current workers
            logger.debug("Activate worker %s", conf['name'])
            self.worker_pool.add(conf)

    def remove(self, workerset):
        if not self.is_my_process:
            return

        for function in workerset:
            conf = function._tm_worker
            logger.debug("Disable worker %s", conf['name'])
            self.worker_pool.workers.pop(conf['name'], None)


def define_arguments(parser):
    define_core_arguments(parser)
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

        self.worker_pool = WorkerPoolService(
            app=self, setproctitle=setproctitle, name=u'worker pool',
            task_queue=task_queue, event_queue=event_queue)
        self.services.append(self.worker_pool)

        self.scheduler = SchedulerService(
            app=self, setproctitle=setproctitle, name=u'scheduler',
            task_queue=task_queue, event_queue=event_queue)
        self.services.append(self.scheduler)

        self.bootstrap(args=args, environ=environ)
        config = self.config

        # Run temboard-agent as a background daemon.
        if (config.temboard.daemonize):
            daemonize(config.temboard.pidfile)

        logger.info("Starting main process.")

        self.start_datetime = datetime.datetime.now()
        self.reload_datetime = None
        self.pid = os.getpid()
        self.user = getpass.getuser()

        # Purge all data queues at start time excepting metrics &
        # notifications.
        purge_queue_dir(
            config.temboard['home'],
            ['metrics.q', 'notifications.q', 'notifications_last_10.q']
        )

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
