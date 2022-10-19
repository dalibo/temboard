# Managed file-based SQL query for agent
#
# Implement a dict-like interface to loading SQL queries from files.
#
# Implement SQL edition using pragma comment. Line ending with
#
# -- pragma:pg_version_min XXXXXX
#
# or
#
# -- pragma:pg_version_max XXXXXX
#
# Are filtered accodring to instance pg_version (from discovery). See app.py
# for initialization. Version comparison is inclusive. To include a line up to
# a major version, use 149999.
#
import os.path
import re
from textwrap import dedent


class QueryFiler(dict):
    # A dict loading it's values from SQL files in a directory.

    def __init__(self, path):
        self.path = path
        super(QueryFiler, self).__init__()

    def load(self, pg_version=None):
        fmt = dedent("""\
        -- From %s
        %s
        """)

        for path in self.iter_files():
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            with open(path) as fo:
                if pg_version:
                    sql = ''.join(filter(
                        lambda l: filter_pragma_version(l, pg_version),
                        fo,
                    ))
                else:
                    sql = fo.read()
            self[name] = fmt % (path, sql)

    def iter_files(self):
        for filename in os.listdir(self.path):
            if not filename.endswith('.sql'):
                continue
            yield self.path + '/' + filename


_pragma_version_re = re.compile(r'-- pragma:pg_version_(min|max) (\d{6})')


def filter_pragma_version(line, pg_version):
    match = _pragma_version_re.search(line)
    if not match:
        return True

    operator = match.group(1)
    target = int(match.group(2))

    if 'min' == operator and target <= pg_version:
        return True
    if 'max' == operator and pg_version <= target:
        return True

    return False
