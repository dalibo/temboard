# This module provide an undocumented feature mainly for development purpose:
# execute a task foreground.
#
# Usage: python -m temboardui.runtask [options] worker_name
#
# Note that our home-made background task implementation, we use a different
# semantic that state of the art background task implemtation:
#
# a task function is called a worker
# a worker process is called workerpool
# a message is called a task
# the message broker is called taskmanager
#

import logging
import sys
from ast import literal_eval
from textwrap import dedent

from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..model import check_schema
from .app import app


logger = logging.getLogger(__name__)


@app.command
class RunTask(SubCommand):
    """ Run a task foreground. """

    def define_arguments(self, parser):
        parser.description = dedent("""\

        Run a task foreground. Some tasks won't work foreground because they
        requires task manager processes.

        Use this only for testing, debugging and development.

        """)

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
            help="Worker arguments as Python literals.",
        )

    def main(self, args):
        workers = iter_workers(self.app.worker_pool.worker_pool)

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

        check_schema()

        worker(self.app, *worker_args)


def iter_workers(pool):
    for name, config in pool.workers.items():
        mod = sys.modules[config['module']]
        fn = getattr(mod, config['function'])
        yield fn
