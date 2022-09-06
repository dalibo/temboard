import os.path


class QueryFiler(dict):
    # A dict loading it's values from SQL files in a directory.

    def __init__(self, path):
        self.path = path
        super(QueryFiler, self).__init__()

    def load(self):
        for path in self.iter_files():
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            with open(path) as fo:
                self[name] = fo.read()

    def iter_files(self):
        for filename in os.listdir(self.path):
            if not filename.endswith('.sql'):
                continue
            yield self.path + '/' + filename
