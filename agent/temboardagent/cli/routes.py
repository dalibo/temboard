import logging
import sys
from itertools import chain

from bottle import default_app

from ..routing import get_routes
from ..toolkit.app import SubCommand
from .app import app


logger = logging.getLogger(__name__)


@app.command
class Routes(SubCommand):
    """ Show HTTP routing table."""

    def main(self, args):
        routes = chain(iter_routes(get_routes()), iter_bottle_routes())
        for path, method, callback in sorted(routes):
            doc = callback.__doc__ or ''
            try:
                title = doc.splitlines()[0]
            except IndexError:
                title = ''
            print("    %6.6s %-64s  %s" % (method, path, title))

        return 0


def iter_routes(routes):
    for route in routes:
        mod = sys.modules[route['module']]
        callback = getattr(mod, route['function'])
        yield route['path'].decode('ascii'), route['http_method'], callback


def iter_bottle_routes():
    bottle = default_app()
    for route in bottle.routes:
        yield route.rule, route.method, route.callback
