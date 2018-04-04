import logging
import os
import signal

from .utils import setproctitle


logger = logging.getLogger(__name__)


class Service(object):
    # Manage long running process. This include setup, signal management and
    # loop.

    def __init__(self, app, name=None):
        self.app = app
        self.name = name

    def __enter__(self):
        signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        self.sighup = False

    def __exit__(self, *a):
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    def sighup_handler(self, *a):
        self.sighup = True

    def sigterm_handler(self, *a):
        os._exit(1)

    def run(self):
        if self.name:
            setproctitle('temboard-agent: %s' % self.name)

        self.setup()
        self.serve()

    def serve(self):
        with self:
            while True:
                if self.sighup:
                    self.sighup = False
                    self.reload()
                self.serve1()

    def reload(self):
        self.app.reload()

    def setup(self):
        # This method is called once before looping to prepare the service:
        # bind address, setup SSL, etc.
        pass

    def serve1(self):
        # This method is called by the loop and must serve one request/task.
        # This method should not block for too long waiting for work to be
        # done. Reload is applied between two calls of this method.
        raise NotImplemented
