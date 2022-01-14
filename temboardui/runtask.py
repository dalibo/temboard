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
import logging.config
import sys
from argparse import (
    ArgumentParser,
    SUPPRESS as UNDEFINED_ARGUMENT,
)
from ast import literal_eval

from .toolkit.errors import UserError
from .__main__ import (
    check_schema,
    legacy_bootstrap,
    list_options_specs,
    map_pgvars,
    TemboardApplication,
)

# Avoid using `__name__` which could be `__main__`
module_name = 'temboardui.runtask'

logger = logging.getLogger(module_name)


class TaskApplication(TemboardApplication):

    def main(self, argv, environ):

        # C O N F I G U R A T I O N

        parser = ArgumentParser(
            prog=module_name,
            description="Run a single task foreground.",
            argument_default=UNDEFINED_ARGUMENT,
        )
        parser.add_argument(
            '-c', '--config',
            action='store', dest='temboard_configfile',
            help="Configuration file", metavar='CONFIGFILE',
        )
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
        environ = map_pgvars(environ)
        self.bootstrap(args=args, environ=environ)

        self.log_versions()
        logging.getLogger('alembic').setLevel(logging.WARN)
        # Manage logging_debug default until we use toolkit OptionSpec.
        legacy_bootstrap(self.config)

        self.apply_config()

        check_schema(self.config)

        # E X E C U T I O N

        workers = iter_workers(self.webapp.workersets)

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


def iter_workers(workersets):
    for workerset in workersets:
        for worker in workerset:
            yield worker


main = TaskApplication(
    specs=list_options_specs(),
    with_plugins="temboard.plugins",
)


if __name__ == "__main__":
    sys.exit(main())
