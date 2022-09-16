# Note that our home-made background task implementation uses a different
# semantic that state of the art background task implemtation:
#
# a task function is called a worker
# a worker process is called workerpool
# a message is called a task
# the message broker is called taskmanager
#

import logging.config

from .app import app
from ..toolkit.app import SubCommand
from ..toolkit.taskmanager import FlushTasksMixin, RunTaskMixin
from ..toolkit.errors import UserError


logger = logging.getLogger(__name__)


@app.command
class Tasks(SubCommand):
    """ Manage background tasks. """

    def main(self, args):
        raise UserError("Missing sub-command. See --help for details.")


@Tasks.command
class Flush(FlushTasksMixin, SubCommand):
    """ Flush all tasks. """


@Tasks.command
class Run(RunTaskMixin, SubCommand):
    """ Run a task foreground. """

    def main(self, args):
        workers = self.iter_workers()

        if '?' == args.worker_name:
            self.print_workers(workers)
        else:
            worker, worker_args = self.compute_worker_args(workers, args)
            worker(*worker_args)
        return 0
