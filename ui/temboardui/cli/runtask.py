import logging

from ..toolkit.app import SubCommand
from ..toolkit.taskmanager import RunTaskMixin
from ..model import check_schema
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
            check_schema()
            worker(*worker_args)
        return 0
