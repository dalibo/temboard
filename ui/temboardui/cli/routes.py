import logging
from itertools import chain

from flask import current_app

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
        rules = self.app.tornado_app.wildcard_router.rules
        routes = chain(iter_tornado_routes(rules), iter_flask_routes())

        if args.sort:
            logger.debug("Sorting routes alphabetically.")
            routes = sorted(routes, key=lambda x: (x[1], x[0]))
        else:
            logger.debug("Listing routes by matching order.")

        for method, path in routes:
            print("    %6.6s %-64s" % (method, path))

        return 0


def iter_flask_routes():
    for rule in current_app.url_map.iter_rules():
        for method in rule.methods:
            if method in ('OPTIONS', 'HEAD'):
                continue
            yield method, rule.rule


def iter_tornado_routes(rules):
    for rule in rules:
        if 'fallback' in rule.target_kwargs:
            # Skip fallback to Flask routes.
            continue

        # Fallback for static handlers
        methods = rule.target_kwargs.get('methods', ['GET'])
        path = rule.matcher.regex.pattern
        for method in methods:
            yield method, path
