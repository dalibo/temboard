import sys

from .web.flask import create_app
from .cli.app import app
from .model import QUERIES
from .model.queries import load_queries


def main():
    flask = create_app(app)
    flask.app_context().push()

    __import__(__package__ + '.web.routes')

    # Load sub commands.
    __import__(__package__ + '.cli.generate_key')
    __import__(__package__ + '.cli.migratedb')
    __import__(__package__ + '.cli.query_agent')
    __import__(__package__ + '.cli.routes')
    __import__(__package__ + '.cli.runtask')
    __import__(__package__ + '.cli.schedule')
    __import__(__package__ + '.cli.serve')
    __import__(__package__ + '.cli.web')

    QUERIES.update(load_queries())

    return app()


if '__main__' == __name__:
    sys.exit(main())
