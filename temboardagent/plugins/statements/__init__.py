import logging

from temboardagent.errors import UserError
from temboardagent.routing import RouteSet


logger = logging.getLogger(__name__)
routes = RouteSet(prefix=b"/statements")


@routes.get(b"/", check_key=True)
def get_statements(http_context, app):
    return {}


class StatementsPlugin(object):
    PG_MIN_VERSION = 90500
    option_specs = []

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def load(self):
        pg_version = self.app.postgres.fetch_version()
        if pg_version < self.PG_MIN_VERSION:
            msg = "%s is incompatible with Postgres below 9.5" % (
                self.__class__.__name__)
            raise UserError(msg)

        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.option_specs)
