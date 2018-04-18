# coding: utf-8

from __future__ import unicode_literals

import logging
import os
from multiprocessing import Process
import signal
from time import sleep
import sys

from .errors import UserError
from .utils import setproctitle


logger = logging.getLogger(__name__)


class Service(object):
    # Manage long running process. This include setup, signal management and
    # loop.
    #
    # There is two kind of services : main service and child services. Main
    # service is responsible to duplicate signals to children with
    # ServicesManager.

    def __init__(self, app, name=None, services=None):
        self.app = app
        self.name = name
        # Must be None for children or ServicesManager instance for main
        # service. Used to propagate signals. See reload() method.
        self.services = services
        self.pid = None
        self.parentpid = None

    def __unicode__(self):
        return '%s (pid=%s)' % (self.name, self.pid)

    def __enter__(self):
        self.sigchld = False
        if self.services:
            signal.signal(signal.SIGCHLD, self.sigchld_handler)
        signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        self.sighup = False

    def __exit__(self, *a):
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    def check_parent_running(self):
        if self.parentpid is None:
            # If no parentpid, we are the main service. We are running.
            return True

        try:
            os.kill(self.parentpid, 0)
            return True
        except OSError:
            return False

    def sigchld_handler(self, *a):
        self.sigchld = True

    def sighup_handler(self, *a):
        self.sighup = True

    def sigterm_handler(self, *a):
        logger.info("Terminated.")
        sys.exit(1)

    def apply_config(self):
        pass

    def run(self):
        if self.name:
            setproctitle('temboard-agent: %s' % self.name)

        self.setup()
        try:
            self.serve()
        except KeyboardInterrupt:
            logger.info("Interrupted.")
            sys.exit(1)

    def serve(self):
        with self:
            while True:
                if not self.check_parent_running():
                    logger.warn(
                        "Parent process %d is dead. Committing suicide.",
                        self.parentpid)
                    sys.exit(1)

                if self.sigchld:
                    self.sigchld = False
                    if self.services:
                        self.services.check()

                if self.sighup:
                    self.sighup = False
                    self.reload()

                self.serve1()

    def reload(self):
        self.app.reload()
        if self.services:
            self.services.reload()

    def setup(self):
        # This method is called once before looping to prepare the service:
        # bind address, setup SSL, etc.
        pass

    def serve1(self):
        # This method is called by the loop and must serve one request/task.
        # This method should not block for too long waiting for work to be
        # done. Reload is applied between two calls of this method.
        raise NotImplemented


class ServicesManager(object):
    # Manage child services : starting in background, tracking PID, replicating
    # signals, checking status, stopping and killing.
    #
    # Add a service with services_manager.add(Service(…)).
    #
    # As a context manager, services are started on enter and stopped-killed on
    # exit.

    def __init__(self):
        self.processes = []
        self.pid = os.getpid()

    def __enter__(self):
        self.start()

    def __exit__(self, *a):
        self.stop()
        logger.debug("Waiting background services.")
        sleep(0.25)
        self.kill()

    def add(self, service):
        service.parentpid = self.pid
        self.processes.append(Process(target=service.run, name=service.name))

    def start(self):
        for process in self.processes:
            process.start()

    def reload(self):
        for process in self.processes:
            os.kill(process.pid, signal.SIGHUP)

    def check(self):
        for p in self.processes[:]:
            logger.debug("Checking child %s (%s).", p.name, p.pid)
            if not p.is_alive():
                logger.debug("%s (%s) is dead.", p.name, p.pid)
                self.processes.remove(p)
                msg = "Child %s (%s) died." % (p.name, p.pid)
                raise UserError(msg)

    def stop(self):
        for process in self.processes:
            process.terminate()

    def kill(self, timeout=5, step=0.5):
        while timeout > 0:
            processes = [p for p in self.processes if p.is_alive()]
            if not processes:
                break
            sleep(step)
            timeout -= step

        for process in processes:
            logger.warn("Killing %s.", process)
            os.kill(process.pid, signal.SIGKILL)
