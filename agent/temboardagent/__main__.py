import sys

from bottle import default_app

from .cli.app import app
from .web.app import create_app


def main():
    default_app.pop()  # Remove default app.
    default_app.push(create_app(app))

    # Import core HTTP routes
    __import__(__package__ + '.web.core')

    # Import commands
    __import__(__package__ + '.cli.discover')
    __import__(__package__ + '.cli.fetch_key')
    __import__(__package__ + '.cli.register')
    __import__(__package__ + '.cli.routes')
    __import__(__package__ + '.cli.runscript')
    __import__(__package__ + '.cli.serve')
    __import__(__package__ + '.cli.tasks')
    __import__(__package__ + '.cli.web')
    return app()


if '__main__' == __name__:
    sys.exit(main())
