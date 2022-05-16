import logging

from ..toolkit.app import SubCommand
from .app import app


logger = logging.getLogger(__name__)


@app.command
class Routes(SubCommand):
    """List HTTP routes map."""

    def define_arguments(self, parser):
        parser.add_argument(
            "--sort",
            action='store_true', default=False,
            help="Sort routes alphabetically",
        )

    def main(self, args):
        rules = self.app.webapp.wildcard_router.rules
        routes = iter_route(rules)

        if args.sort:
            logger.debug("Sorting routes alphabetically.")
            routes = sorted(routes, key=lambda x: (x[1], x[0]))
        else:
            logger.debug("Listing routes by matching order.")

        for method, path in routes:
            print("    %6.6s %-64s" % (method, path))

        return 0


def iter_route(rules):
    for rule in rules:
        # Fallback for static handlers
        methods = rule.target_kwargs.get('methods', ['GET'])
        path = rule.matcher.regex.pattern
        for method in methods:
            yield method, path
