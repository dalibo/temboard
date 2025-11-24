from temboardtoolkit import services
from temboardtoolkit.app import SubCommand

from ..model import check_schema
from .app import app


@app.command
class Serve(SubCommand):
    """Combined web server and background workers."""

    is_service = True

    def main(self, args):
        check_schema()
        self.app.config.load_signing_key()

        services.run(self.app.webservice, self.app.scheduler, self.app.worker_pool)
