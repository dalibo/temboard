# Mimic asyncio API with synchronous code.
import logging
import os
import signal

logger = logging.getLogger(__name__)


class Service:
    # Mixin for scheduler, worker pool and agent httpd services
    # Manages sync loop and signals.
    name = None

    def __init__(self, app):
        self.app = app
        self.ppid = None

    def __str__(self):
        return self.name

    # interface for services.run
    def create_loop(self):
        return Loop(self, self.ppid)

    # Interface for SignalMultiplexer
    def sighup_handler(self, *a):
        self.app.reload()


class Loop:
    def __init__(self, service, ppid=None):
        self.service = service
        self.signalmngr = SignalManager()
        self.running = False
        # If not None, enable parent pid check.
        self.ppid = ppid

    def __repr__(self):
        return "<Loop %s>" % self.service

    # Interface for SignalMultiplexer
    def add_signal_handler(self, sig, handler, *a):
        self.signalmngr[sig] = handler

    def remove_signal_handler(self, sig):
        if sig not in self.signalmngr:
            return
        del self.signalmngr[sig]
        if self.running:
            signal.signal(sig, signal.SIG_DFL)

    # Interface for services.run
    def start(self):
        with self.signalmngr:
            self.running = True
            while self.running:
                if self._stop_with_parent():
                    break

                self.service.accept()

    def stop(self):
        self.running = False

    def close(self):
        self.running = False

    def _stop_with_parent(self):
        if self.ppid is None:  # Don't check parent.
            return
        # If ppid changed (parent exited), stop the loop.
        self.running = os.getppid() == self.ppid
        if not self.running:
            logger.info("Parent process exited. Exiting. ppid=%s", self.ppid)
        return not self.running


class SignalManager(dict):
    # Context manager for synchronous signal handling.

    def __enter__(self):
        for sig, handler in self.items():
            signal.signal(sig, handler)
        self._registered = self.keys()

    def __exit__(self, *exc):
        for sig in self._registered:
            signal.signal(sig, signal.SIG_DFL)
        del self._registered
