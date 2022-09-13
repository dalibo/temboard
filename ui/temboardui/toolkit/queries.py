import os.path
from textwrap import dedent


class QueryFiler(dict):
    # A dict loading it's values from SQL files in a directory.

    def __init__(self, path):
        self.path = path
        super(QueryFiler, self).__init__()

    def load(self):
        fmt = dedent("""\
        -- From %s
        %s
        """)

        for path in self.iter_files():
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            with open(path) as fo:
                sql = fo.read()
            self[name] = fmt % (path, sql)

    def iter_files(self):
        for filename in os.listdir(self.path):
            if not filename.endswith('.sql'):
                continue
            yield self.path + '/' + filename
