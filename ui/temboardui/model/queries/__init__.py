import os.path


QUERIESDIR = os.path.dirname(__file__)


def load_queries():
    return dict(iter_queries(iter_queries_files(QUERIESDIR)))


def iter_queries(paths):
    for path in paths:
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        with open(path) as fo:
            yield name, fo.read()


def iter_queries_files(directory):
    for filename in os.listdir(directory):
        if not filename.endswith('.sql'):
            continue
        yield directory + '/' + filename
