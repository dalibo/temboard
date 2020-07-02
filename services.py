# coding: utf-8
#
# This module implements background service management.
#
# Background service management features:
# - Proper starting and killing of background service.
# - proctitle definition.
# - SIGTERM and SIGHUP propagation.
# - SIGCHLD management. No zombie.
# - Child suicide on parent death.
#
# Two classes help manage multiple services: Service and ServicesManager.
#
# Each long running process must have it's own Service instance. Service class
# is used both to manage current process service as well as reference to
# manipulate long-runnning child process.
#
# ServicesManager class is kind of an init system for the main process. It is
# responsible of starting, killing and propagating signals to child processes.
# Service instance of main process service must have a reference to
# ServicesManager.

import logging
import os
import signal
import sys
from multiprocessing import Process
from time import sleep

from .errors import UserError


logger = logging.getLogger(__name__)


class Service(object):
    # Manage long running process. This include setup, signal management and
    # loop.
    #
    # There is two kind of services : main service and child services. Main
    # service is responsible to propagate signals to children with
    # ServicesManager.

    def __init__(self, app, name=None, services=None, setproctitle=None):
        self.app = app
        self.name = name
        self.logname = name or u'service'
        # Must be None for children or ServicesManager instance for main
        # service. Used to propagate signals. See reload() method.
        self.services = services
        self.setproctitle = setproctitle

        self.parentpid = None
        # Once the process is forked to run the service loop, we still use this
        # object in parent process to manage the child process. So we flag here
        # whether the service has forked in it's own process. Must be updated
        # in parent process once the service is forked. See
        # ServicesManager.start().
        self.is_my_process = True

    def __unicode__(self):
        return self.logname

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
        logger.info(u"%s terminated.", self)
        sys.exit(1)

    def apply_config(self):
        pass

    def run(self):
        if self.name and self.setproctitle:
            self.setproctitle(self.name)
        logger.info(u"Starting %s.", self)

        self.setup()
        try:
            self.serve()
        except KeyboardInterrupt:
            logger.info(u"%s interrupted.", self)
            sys.exit(1)

    def serve(self):
        with self:
            logger.debug(u"Entering %s loop.", self)
            while True:
                if not self.check_parent_running():
                    logger.warn(
                        u"Parent process %d is dead. Committing suicide.",
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
        raise NotImplementedError


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
        logger.debug(u"Waiting background services.")
        sleep(0.125)
        self.kill()

    def add(self, service):
        service.parentpid = self.pid
        self.processes.append(
            (service, Process(target=service.run, name=service.name)))

    def start(self):
        for service, process in self.processes:
            process.start()
            service.is_my_process = False

    def reload(self):
        for _, process in self.processes:
            os.kill(process.pid, signal.SIGHUP)

    def check(self):
        for i in self.processes[:]:
            _, p = i
            logger.debug(u"Checking child %s (%s).", p.name, p.pid)
            if not p.is_alive():
                logger.debug("%s (%s) is dead.", p.name, p.pid)
                self.processes.remove(i)
                msg = u"Child %s (%s) died." % (p.name, p.pid)
                raise UserError(msg)

    def stop(self):
        for _, process in self.processes:
            process.terminate()

    def kill(self, timeout=5, step=0.5):
        while timeout > 0:
            processes = [p for _, p in self.processes if p.is_alive()]
            if not processes:
                break
            sleep(step)
            timeout -= step

        for process in processes:
            logger.warning(u"Killing %s.", process)
            os.kill(process.pid, signal.SIGKILL)
