# Mimic asyncio API with synchronous code.
import logging
import os
import signal

logger = logging.getLogger(__name__)


class Service:
    # Mixin for scheduler and worker pool services
    # Manages sync loop and signals.
    name = None

    def __init__(self, app):
        self.app = app

    def __str__(self):
        return self.name

    # interface for services.run
    def create_loop(self):
        return Loop(self)

    # Interface for SignalMultiplexer
    def sighup_handler(self, *a):
        self.app.reload()


class Loop:
    def __init__(self, service):
        self.service = service
        self.signalmngr = SignalManager()
        self.running = False

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
            ppid = os.getppid()
            self.running = True
            while self.running:
                if self._stop_with_parent(ppid):
                    break

                self.service.accept()

    def stop(self):
        self.running = False

    def close(self):
        self.running = False

    def _stop_with_parent(self, ppid):
        self.running = os.getppid() == ppid
        if not self.running:
            logger.info("Parent process exited. Exiting. ppid=%s", ppid)
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
