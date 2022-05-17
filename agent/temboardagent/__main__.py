import sys

from .cli.app import app


def main():
    # Import main HTTP routes
    __import__(__package__ + '.api')

    # Import commands
    __import__(__package__ + '.cli.register')
    __import__(__package__ + '.cli.routes')
    __import__(__package__ + '.cli.runtask')
    __import__(__package__ + '.cli.serve')
    __import__(__package__ + '.cli.web')
    return app()


if '__main__' == __name__:
    sys.exit(main())
