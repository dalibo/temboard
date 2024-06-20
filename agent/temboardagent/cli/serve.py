import logging
import os

from ..plugins.monitoring import db
from ..toolkit import services
from ..toolkit.app import SubCommand
from .app import app

logger = logging.getLogger(__name__)


@app.command
class Serve(SubCommand):
    """Combined web and worker services."""

    is_service = True

    def main(self, args):
        # Purge all legacy data queues
        home = self.app.config.temboard.home
        if os.path.exists(home):
            [
                os.remove(os.path.join(home, f))
                for f in os.listdir(home)
                if f.endswith(".q")
            ]

        if "monitoring" in self.app.config.temboard.plugins:
            logger.info("Resetting monitoring data.")
            db.bootstrap(self.app.config.temboard.home, "monitoring.db")

        self.app.config.load_signing_key()
        self.app.discover.refresh()
        self.app.discover.write()

        return services.run(self.app.httpd, self.app.scheduler, self.app.worker_pool)
