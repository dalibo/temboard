import re
from pgconf.filemgmt import (
    ConfigurationFileManager,
    read_file_content,
    save_file_content,
)
from temboardagent.errors import HTTPError


class HBAManager(ConfigurationFileManager):

    @classmethod
    def get_entries(self, filepath, version=None):
        entries = []
        for raw_line in read_file_content(filepath, version).split('\n'):
            entry = HBAEntry.parse(raw_line)
            if entry is not None:
                entries.append(entry)
        return entries

    @classmethod
    def save_entries(self, filepath, hba_entries, new_version=False):
        filecontent = ''
        for hba_entry in hba_entries:
            filecontent += str(hba_entry)
        return save_file_content(filecontent, filepath, new_version)

    @classmethod
    def options(self, conn):
        connections = ["local", "host", "hostssl", "hostnossl"]
        auth_methods = ["trust", "reject", "md5", "password", "gss", "sspi",
                        "ident", "peer", "ldap", "radius", "cert", "pam"]
        databases = ["all", "sameuser", "samerole", "replication"]
        users = ["all"]
        # Get users
        conn.execute("SELECT usename FROM pg_user ORDER BY usename ASC")
        for row in conn.get_rows():
            users.append(row['usename'])
        # Get groups containgin users
        conn.execute("""
            SELECT rolname
            FROM pg_user
            JOIN pg_auth_members
            ON (pg_user.usesysid=pg_auth_members.member)
            JOIN pg_roles
            ON (pg_roles.oid=pg_auth_members.roleid) ORDER BY rolname ASC
        """)
        for row in conn.get_rows():
            users.append("+%s" % (row['rolname']))
        # Get databases name
        conn.execute("""
            SELECT datname
            FROM pg_database
            WHERE NOT datistemplate
            ORDER BY datname ASC
        """)
        for row in conn.get_rows():
            databases.append(row['datname'])
        return {'connections': connections,
                'databases': databases,
                'users': users,
                'auth_methods': sorted(auth_methods)}


class HBAComment:

    def __init__(self, comment=''):
        self.comment = comment

    def __repr__(self):
        return "# %s\r\n" % (self.comment)


class HBAEntry:

    def __init__(self,
                 connection='',
                 database='',
                 user='',
                 address='',
                 auth_method='',
                 auth_options=''):
        self.connection = connection
        self.database = database
        self.user = user
        self.address = address
        self.auth_method = auth_method
        self.auth_options = auth_options

    def lazy_check(self):
        if self.connection not in ['host', 'hostssl', 'hostnossl', 'local']:
            raise HTTPError(406, "Invalid connection: %s" % (self.connection))
        if len(self.database) < 1:
            raise HTTPError(406, "Invalid database: %s" % (self.database))
        if len(self.user) < 1:
            raise HTTPError(406, "Invalid user: %s" % (self.user))
        if self.connection != 'local' and \
           len(self.address) == 0:
            raise HTTPError(406, "An address is required for method '%s'." %
                                 (self.connection))
        if len(self.auth_method) == 0:
            raise HTTPError(406, "Authentication method must be set.")

    def __repr__(self):
        row = "%s  %s  %s" % (
                self.connection,
                self.database,
                self.user)
        if self.connection is not 'local':
            row += " %s" % (self.address)
        row += " %s %s\r\n" % (self.auth_method, self.auth_options)
        return row

    @classmethod
    def parse(cls, raw):
        raw = raw.strip()
        if raw.startswith('#'):
            return HBAComment(raw.strip()[1:])
        if not raw.startswith('#') and len(raw) > 0:
            p_anything = r'([^\s]+(?<!\s))'
            p_anything_end = r'(\s*[^#]+)?(.*)$'
            p_connection_host = r'(host|hostssl|hostnossl)'
            p_connection_local = r'(local)'
            p_address = r'([0-9a-fA-F\.:]+/[0-9]+(?<!\s))'
            p_ip_address = r'([0-9a-fA-F\.:]+(?<!\s))'
            p_ip_mask = r'([0-9a-fA-F\.:]+(?<!\s))'

            r_host_address = re.compile(
                r'^'
                + p_connection_host + r'\s+'
                + p_anything + r'\s+'
                + p_anything + r'\s+'
                + p_address + r'\s+'
                + p_anything
                + p_anything_end)
            r_host_ip_address = re.compile(
                r'^'
                + p_connection_host + r'\s+'
                + p_anything + r'\s+'
                + p_anything + r'\s+'
                + p_ip_address + r'\s+'
                + p_ip_mask + r'\s+'
                + p_anything
                + p_anything_end)
            r_local = re.compile(
                r'^'
                + p_connection_local + r'\s+'
                + p_anything + r'\s+'
                + p_anything + r'\s+'
                + p_anything
                + p_anything_end)

            m_host = r_host_address.match(raw.strip())
            if m_host:
                return cls(
                    m_host.group(1),
                    m_host.group(2),
                    m_host.group(3),
                    m_host.group(4),
                    m_host.group(5),
                    m_host.group(6).strip()
                    if m_host.group(6)
                    and not m_host.group(6).strip().startswith('#')
                    else '')

            m_host = r_host_ip_address.match(raw.strip())
            if m_host:
                return cls(
                    m_host.group(1),
                    m_host.group(2),
                    m_host.group(3),
                    "%s %s" % (m_host.group(4), m_host.group(5)),
                    m_host.group(6),
                    m_host.group(7).strip()
                    if m_host.group(7)
                    and not m_host.group(7).strip().startswith('#')
                    else '')

            m_local = r_local.match(raw.strip())
            if m_local:
                return cls(
                    m_local.group(1),
                    m_local.group(2),
                    m_local.group(3),
                    '',
                    m_local.group(4),
                    m_local.group(5).strip()
                    if m_local.group(5)
                    and not m_local.group(5).strip().startswith('#')
                    else '')
