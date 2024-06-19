# Setup and run Prometheus for temBoard.
#
# This is a standalone Prometheus instance, for testing purpose only.
# It is not intended to be used in production.
#
# Until 9.0 the command is not exposed.
# Run with python -m temboardui.cli.prometheus.
#
# Requires a running temboard instance aside to expose metrics.
#
# Dev Grafana (http://localhost:3000) is setup to use this Prometheus as
# `temBoard prometheus` with a dedicated dashboard.
#
import logging
import sys

from .. import prometheus
from ..toolkit import services
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from .app import app

logger = logging.getLogger(__package__ + ".prometheus")


@app.command
class Prometheus(SubCommand):
    """Standalone Prometheus for temBoard.

    For testing purpose only.

    """

    is_service = True

    def main(self, args):
        if not self.app.config.monitoring.prometheus:
            raise UserError("missing prometheus binary")

        return services.run(prometheus.Manager(app=self.app))


if "__main__" == __name__:
    from ..__main__ import main

    sys.exit(main(argv=["prometheus"] + sys.argv[1:]))
