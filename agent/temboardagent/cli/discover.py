import logging
import sys

from ..toolkit.app import SubCommand
from .app import app


logger = logging.getLogger(__name__)


@app.command
class Discover(SubCommand):
    """Introspect system and PostgreSQL instance."""

    def main(self, args):
        self.app.discover.refresh()
        self.app.discover.write()
        self.app.discover.write(sys.stdout)
        logger.debug("Discover etag is %s.", self.app.discover.etag)
        return 0
