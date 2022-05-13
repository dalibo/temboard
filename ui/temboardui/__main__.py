import sys

from .cli.app import app


def main():
    # Load sub commands.
    __import__(__package__ + '.cli.migratedb')
    __import__(__package__ + '.cli.runtask')
    __import__(__package__ + '.cli.serve')

    return app()


if '__main__' == __name__:
    sys.exit(main())
