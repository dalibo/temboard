import sys

from .cli.app import app


def main():
    # Load sub commands.
    __import__(__package__ + '.cli.migratedb')
    __import__(__package__ + '.cli.query_agent')
    __import__(__package__ + '.cli.routes')
    __import__(__package__ + '.cli.runtask')
    __import__(__package__ + '.cli.serve')
    __import__(__package__ + '.cli.web')

    return app()


if '__main__' == __name__:
    sys.exit(main())
