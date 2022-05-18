import logging
import sys

from ..routing import get_routes
from ..toolkit.app import SubCommand
from .app import app


logger = logging.getLogger(__name__)


@app.command
class Routes(SubCommand):
    """ Show HTTP routing table."""

    def main(self, args):
        routes = get_routes()
        for route in sorted(routes, key=route_sort_key):
            method = route['http_method']
            path = route['path'].decode('utf-8')
            mod = sys.modules[route['module']]
            fn = getattr(mod, route['function'])
            doc = fn.__doc__ or ''
            try:
                title = doc.splitlines()[0]
            except IndexError:
                title = ''
            print("    %6.6s %-64s  %s" % (method, path, title))

        return 0


def route_sort_key(route):
    return route['path'], route['http_method']
