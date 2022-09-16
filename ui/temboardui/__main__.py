#
# There is three app objects in temBoard. One for Tornado, Flask and temBoard
# itself.
#
# Tornado's app is implemented and instanciated in t.w.tornado. Tornado's app
# holds Tornado routes. Tornado's app is a Tornado HTTP server delegate.
#
# Flask app is implemented in t.w.flask and instanciated here in t.__main__,
# accessible through flask.current_app thread local. Flask app holds Flask
# routes. Flask app is a WSGI app.
#
# temBoard app is implemented and instanciated in t.c.app. temBoard app holds
# configuration, CLI definition and controls execution of the service. temBoard
# app is a CLI entrypoint.
#
# Each of this app has different purpose, configuration handling and
# initialization process. This is quite messy and needs redesign.
#

import sys

from .web.flask import create_app
from .cli.app import app
from .model import QUERIES


def main():
    flask = create_app(app)
    flask.app_context().push()

    # Import main routes
    __import__(__package__ + '.handlers.core')
    __import__(__package__ + '.web.routes')

    # Load sub commands.
    __import__(__package__ + '.cli.apikey')
    __import__(__package__ + '.cli.generate_key')
    __import__(__package__ + '.cli.migratedb')
    __import__(__package__ + '.cli.query_agent')
    __import__(__package__ + '.cli.register_instance')
    __import__(__package__ + '.cli.routes')
    __import__(__package__ + '.cli.serve')
    __import__(__package__ + '.cli.tasks')
    __import__(__package__ + '.cli.web')

    QUERIES.load()

    return app()


if '__main__' == __name__:
    sys.exit(main())
