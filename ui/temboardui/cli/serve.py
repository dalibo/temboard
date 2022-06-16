from ..daemon import daemonize
from ..model import check_schema
from ..toolkit.app import SubCommand
from ..toolkit.services import ServicesManager
from .app import app


@app.command
class Serve(SubCommand):
    """Combined web server and worker processes."""

    is_service = True

    def main(self, args):
        check_schema()
        self.app.config.load_signing_key()

        # Enable background services with web as main process.
        self.app.webservice.services = services = ServicesManager()
        services.add(self.app.worker_pool)
        services.add(self.app.scheduler)

        # Run temboard as a background daemon.
        if self.app.config.temboard.daemonize:
            daemonize(self.app.config.temboard.pidfile, self.app.config)

        with self.app.webservice.services:
            self.app.webservice.run()
