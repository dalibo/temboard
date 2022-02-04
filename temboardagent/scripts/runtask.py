# This module provide an undocumented feature mainly for development purpose:
# execute a task foreground.
#
# Usage: python -m temboardagent.scripts.runtask [options] worker_name [arg
# ...]
#
# Note that our home-made background task implementation, we use a different
# semantic that state of the art background task implemtation:
#
# a task function is called a worker
# a worker process is called workerpool
# a message is called a task
# the message broker is called taskmanager
#
import logging.config
import sys
from argparse import (
    ArgumentParser,
    SUPPRESS as UNDEFINED_ARGUMENT,
)
from ast import literal_eval

from .agent import list_options_specs
from ..cli import Application
from ..notification import NotificationMgmt
from ..routing import Router
from ..toolkit.app import define_core_arguments
from ..toolkit.errors import UserError
from ..toolkit import taskmanager
from ..toolkit.tasklist.sqlite3_engine import TaskListSQLite3Engine


# Avoid using `__name__` which could be `__main__`
module_name = 'temboardagent.scripts.runtask'

logger = logging.getLogger(module_name)


class TaskApplication(Application):
    PROGRAM = "temboardagent.scripts.runtask"

    def main(self, argv, environ):

        # Required to register plugins.
        self.router = Router()
        self.worker_pool = taskmanager.WorkerPoolService(
            app=self, name='worker pool',
            task_queue=None, event_queue=None)
        self.services.append(self.worker_pool)
        self.scheduler = taskmanager.SchedulerService(
            app=self, name='scheduler',
            task_queue=None, event_queue=None)
        self.scheduler.task_list_engine = TaskListSQLite3Engine(":memory:")
        self.services.append(self.scheduler)

        # C O N F I G U R A T I O N

        parser = ArgumentParser(
            prog=module_name,
            description="Run a single task foreground.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_core_arguments(parser)
        parser.add_argument(
            'worker_name',
            metavar='WORKER',
            help=(
                "Global name of the worker function name to execute."
                " Use ? to list available workers."),
        )
        parser.add_argument(
            'worker_args', nargs='*',
            metavar='ARG',
            default=[],
            help="Worker arguments as Python literals.")

        args = parser.parse_args(argv)
        self.bootstrap(args=args, environ=environ)
        self.log_versions()
        self.apply_config()

        # Bootstraping plugins
        self.bootstrap_plugins()
        # Boostraping action logs table
        NotificationMgmt.bootstrap(self.config)

        # E X E C U T I O N

        workers = iter_workers(self.worker_pool.worker_pool.workers)

        if '?' == args.worker_name:
            for name in sorted(fn.__name__ for fn in workers):
                print(name)
            return 0

        needles = (args.worker_name, args.worker_name + '_worker')
        for worker in workers:
            if worker.__name__ in needles:
                break
        else:
            raise UserError("Unknown worker %s." % args.worker_name)

        worker_args = []
        for arg in args.worker_args:
            try:
                arg = literal_eval(arg)
            except Exception:
                logger.debug("Unknown literal %s, using as raw string.", arg)
            worker_args.append(arg)

        worker(self, *worker_args)

    def bootstrap_plugins(self):
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, 'bootstrap'):
                logger.debug("Boostraping plugin %s", plugin_name)
                plugin.bootstrap()


def iter_workers(workers):
    for name, config in workers.items():
        wrapper = getattr(sys.modules[config['module']], config['function'])
        yield wrapper._tm_function


main = TaskApplication(specs=list_options_specs())


if __name__ == "__main__":
    sys.exit(main())
