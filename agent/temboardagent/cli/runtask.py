# Note that our home-made background task implementation, we use a different
# semantic that state of the art background task implemtation:
#
# a task function is called a worker
# a worker process is called workerpool
# a message is called a task
# the message broker is called taskmanager
#

import logging.config

from ..toolkit.app import SubCommand
from ..toolkit.taskmanager import RunTaskMixin
from .app import app


logger = logging.getLogger(__name__)


@app.command
class RunTask(RunTaskMixin, SubCommand):
    """ Run a task foreground. """

    def main(self, args):
        workers = self.iter_workers()

        if '?' == args.worker_name:
            self.print_workers(workers)
        else:
            worker, worker_args = self.compute_worker_args(workers, args)
            worker(*worker_args)
        return 0
