# services manages foreground and background services.
#
# run() function is the main entry point and should be enough.
# It handles signals, background services, perf metrics and the main loop.
#
# The core concept is the Service. A service is an object responsible to answer
# requests in a dedicated long running process. temBoard has services for
# Tornado web server, task scheduler, worker pool and plain HTTP server.
#
# An IO loop runs the service. Either tornado asyncio loop or a custom stub
# in syncio.py for synchronous loop.
#
# A key feature for good multiprocessing is proper signal handling.
# BackgroundManager handles propagation of signals and proper behaviour on kill
# of parent of child services.
#
# Since POSIX allows one single signal handler per signal, the
# SignalMultiplexer dispatches signals to idoine method of any object passed to
# it. SignalMultiplexer ask the loop to register signal handler.
#
# To test the behaviour of this code, run temBoard live and:
#
# - Type Ctrl+C, everything should stop gracefully.
# - pkill -ef 'temboard: web' -INT, same.
# - pkill -ef 'temboard: web' -TERM, same.
# - pkill -ef 'temboard: web' -KILL: scheduler and worker pool should stop.
# - pkill -ef 'temboard: scheduler' -KILL: scheduler is restarted
# - pkill -ef 'temboard: web' -HUP : all process must reload configuration
# - Tornado autoreload: all processes are restarted.
#
# Same for temBoard agent.


import logging
import os
import signal
import time

from . import proctitle

logger = logging.getLogger(__name__)


def run(main, *backgrounds):
    """Run a main service object function in this process.

    Handle signals for INT, TERM, HUP, CHLD and ALRM.
    Handle background services.
    Handle perf metrics.
    Start the loop provided by the service.
    Returns an exit code.

    Note that BackgroundManager calls this same function for each background
    service.

    """

    proctitle.set(main)
    loop = main.create_loop()
    sgm = SignalMultiplexer(loop)
    sgm.register(LoopStopper(loop))
    sgm.register(main)

    bg = BackgroundManager(loop)
    if backgrounds:
        for service in backgrounds:
            bg.add(service)
        sgm.register(bg)

    main.setup(sgm, bg)
    with sgm, bg:
        logger.debug("Entering %s loop.", main)
        loop.start()
    if hasattr(main, "teardown"):
        main.teardown()
    logger.debug("Done. service=%s", main)
    return 0


def execute(service):
    """Execute an external command in this process.

    Replace current Python program by a service.command.
    Does not return. service.command continues process life.
    """

    if hasattr(service, "setup"):
        service.setup()

    # Close all files except stdin, stdout, stderr.
    for fd in range(3, os.sysconf("SC_OPEN_MAX")):
        try:
            os.close(fd)
        except OSError:
            pass
    os.execvp(service.command[0], service.command)


class LoopStopper:
    def __init__(self, loop):
        self.loop = loop
        self.stopping = False

    # Interface for SignalMultiplexer
    def sigint_handler(self, *a):
        self.loop.stop()
        logger.info("Interrupted.")
        self.stopping = True

    def sigterm_handler(self, *a):
        if self.stopping:
            # Background service receives both SIGINT from terminal and SIGTERM
            # from main process. Prevent restopping on SIGTERM after SIGINT.
            return
        self.loop.stop()
        logger.info("Terminated.")


class BackgroundManager:
    def __init__(self, loop):
        self.loop = loop
        self.services = {}
        self.pids = {}
        self.stopping = False  # Whether to restart on SIGCHLD

    def add(self, service):
        self.services[str(service)] = service

    def __bool__(self):
        return bool(self.services)

    def __enter__(self):
        if not self.services:
            return

        self._read_pids()

        if self.pids:
            logger.debug("Cleaning previous background services.")
            self.kill()
            if self.wait():
                raise Exception("Background services are still alive.")
        self.start()

    def __exit__(self, etype, evalue, etb):
        if not self.services:
            return
        if etype:
            logger.warning("Exiting on error. err=%s", evalue)
        self.stop()

    def start(self):
        """Start unstarted services."""

        for name, service in self.services.items():
            if name in self.pids:
                continue
            self.fork(service)

    def fork(self, service):
        pid = os.fork()
        if pid:  # Parent process
            logger.debug("Background service started. service=%s pid=%d", service, pid)
            self._save_pid(service, pid)
            return pid

        # Child process
        if hasattr(self.loop, "asyncio_loop"):
            # Cleanup parent signals handling.
            # See https://bugs.python.org/issue22087 and https://bugs.python.org/issue21998 for details about asyncio and fork.
            signal.set_wakeup_fd(-1)

        if hasattr(service, "command"):
            execute(service)
        else:
            os._exit(run(service))

    def _read_pids(self):
        for name, service in self.services.items():
            if not hasattr(service, "pidfile"):
                continue
            if not os.path.exists(service.pidfile):
                continue
            with open(service.pidfile) as fo:
                self.pids[name] = int(fo.read().strip())
                logger.debug(
                    "Read pid from pidfile. service=%s pid=%d", name, self.pids[name]
                )

    def _save_pid(self, service, pid):
        self.pids[str(service)] = pid
        if hasattr(service, "pidfile"):
            with open(service.pidfile, "w") as fo:
                fo.write(str(pid))

    def _drop_pid(self, name):
        del self.pids[name]
        s = self.services[name]
        if not hasattr(s, "pidfile"):
            return
        if os.path.exists(s.pidfile):
            os.unlink(s.pidfile)

    def stop(self):
        self.stopping = True
        for name, pid in self.pids.items():
            logger.debug("Terminating background service. service=%s pid=%d", name, pid)
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        time.sleep(0.125)
        if self.wait():
            self.kill()
            # Wait for children. If we don't wait, we'll have zombies.
            self.wait()

    def wait(self, timeout=5, step=0.5):
        """Return true if process are still alive"""
        if not self.services:
            return False

        logger.debug("Waiting background services.")
        while timeout > 0 and self.pids:
            for name, pid in self.pids.copy().items():
                try:
                    pid, status = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    pass
                if pid:
                    self._drop_pid(name)

            time.sleep(step)
            timeout -= step

        return bool(self.pids)

    def kill(self, sig=signal.SIGKILL):
        for name, pid in self.pids.items():
            logger.warning(
                "Signaling background service. service=%s pid=%s signal=%s",
                name,
                pid,
                sig,
            )
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass

    # interface for SignalMultiplexer.
    def sighup_handler(self, *a):
        for pid in self.pids.values():
            os.kill(pid, signal.SIGHUP)

    def sigchld_handler(self, *a):
        if self.stopping:
            return

        for name, service in self.services.items():
            try:
                pid, _ = os.waitpid(self.pids[name], os.WNOHANG)
                if pid == 0:  # Still alive
                    continue
            except ChildProcessError:
                pass

            logger.warning(
                "Background service dead. Restarting. service=%s pid=%s", name, pid
            )
            self._drop_pid(name)

        self.start()

    def sigint_handler(self, *_):
        # If background services got SIGINT too, don't restart them. If only
        # main service received SIGINT, let __exit__ call effective stop().
        self.stopping = True


class SignalMultiplexer:
    def __init__(self, loop):
        # Map signal to handler list.
        self.handlers = {}
        if hasattr(loop, "asyncio_loop"):
            loop = loop.asyncio_loop
        self.loop = loop

    def register(self, handler):
        if hasattr(handler, "sigalrm_handler"):
            self.handlers.setdefault(signal.SIGALRM, []).append(handler.sigalrm_handler)
        if hasattr(handler, "sigchld_handler"):
            self.handlers.setdefault(signal.SIGCHLD, []).append(handler.sigchld_handler)
        if hasattr(handler, "sighup_handler"):
            self.handlers.setdefault(signal.SIGHUP, []).append(handler.sighup_handler)
        if hasattr(handler, "sigint_handler"):
            self.handlers.setdefault(signal.SIGINT, []).append(handler.sigint_handler)
        if hasattr(handler, "sigterm_handler"):
            self.handlers.setdefault(signal.SIGTERM, []).append(handler.sigterm_handler)

    def __enter__(self):
        for sig, handlers in self.handlers.items():
            self.loop.add_signal_handler(sig, self._handle, sig)
        return self

    def __exit__(self, *a):
        for sig, handlers in self.handlers.items():
            self.loop.remove_signal_handler(sig)

    def _handle(self, sig, stack_frame=None):
        for handler in self.handlers.get(sig, []):
            handler(sig, stack_frame)
