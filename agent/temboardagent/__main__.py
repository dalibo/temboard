import sys

from .cli.app import app


def main():
    __import__(__package__ + '.cli.serve')
    __import__(__package__ + '.cli.register')
    __import__(__package__ + '.cli.runtask')
    return app()


if '__main__' == __name__:
    sys.exit(main())
