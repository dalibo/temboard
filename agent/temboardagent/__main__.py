import sys

from .cli.app import app


def main():
    __import__(__package__ + '.cli.serve')
    return app()


if '__main__' == __name__:
    sys.exit(main())
