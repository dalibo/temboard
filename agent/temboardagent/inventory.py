import logging
import platform
import os
import re

from .tools import which, to_bytes
from .command import exec_command


logger = logging.getLogger(__name__)


class Inventory:
    def __init__(self):
        pass


class SysInfo(Inventory):
    def __init__(self):
        self.os = platform.system()

    def cpu_info(self):
        if self.os == 'Linux':
            return self._cpu_info_linux()
        else:
            raise Exception("Unsupported OS.")

    def mem_info(self):
        if self.os == 'Linux':
            return self._mem_info_linux()
        else:
            raise Exception("Unsupported OS.")

    def ip_addresses(self):
        if self.os == 'Linux':
            return self._ip_addresses_linux()
        else:
            raise Exception("Unsupported OS.")

    def file_systems(self):
        if self.os == 'Linux':
            return self._file_systems_linux()
        else:
            raise Exception("Unsupported OS.")

    def find_mount_point(self, path, mount_points):
        if self.os == 'Linux':
            return self._find_mount_point_linux(path, mount_points)
        else:
            raise Exception("Unsupported OS.")

    def _cpu_info_linux(self):
        cpus = []
        # TODO: implement for other OSes
        if self.os != 'Linux':
            return {}
        current_cpu = {}
        with open('/proc/cpuinfo') as f:
            for line in f.read().split("\n"):
                if ':' not in line:
                    continue
                key, value = (part.strip() for part in line.split(':', 1))
                if key == 'processor':
                    current_cpu = {}
                    cpus.append(current_cpu)
                if key in ['core id', 'cpu MHz', 'model name',
                           'cache size', 'processor']:
                    current_cpu[str(re.sub(r' +', '_', key)).lower()] = value
        if cpus:
            return {
                'cpus': cpus,
                'cpu_count': len(cpus)
            }
        return {}

    def _mem_info_linux(self):
        unit_re = re.compile(r'(\d+) ?(\wB)?')
        mem_values = {}
        with open('/proc/meminfo') as f:
            for line in f.read().split("\n"):
                if ':' not in line:
                    continue
                key, value = (part.strip() for part in line.split(':', 1))
                size, unit = unit_re.match(value).groups()
                size = int(size)
                # convert everything to bytes, if a unit is specified
                if unit:
                    size = to_bytes(size, unit[:-1])
                mem_values[key] = size
        return mem_values

    def _ip_addresses_linux(self):
        """Find the host's IP addresses."""
        addrs = []
        try:
            ip = which('ip')
            (rc, out, err) = exec_command([ip, "addr", "show"])
            if rc == 0:
                for line in out.decode('utf8').splitlines():
                    m = re.match(r'^\s+inet ([\d\.]+)/\d+\s', line)
                    if m:
                        addrs.append(m.group(1))

                    m = re.match(r'^\sinet6 ([\dabcdef\:]+)/\d+ scope global',
                                 line)
                    if m:
                        addrs.append(m.group(1))
                return addrs
        except OSError:
            pass

        try:
            ifconfig = which('ifconfig', ['/sbin'])
            (rc, out, err) = exec_command([ifconfig, "-a"])
            if rc == 0:
                for line in out.decode('utf8').splitlines():
                    m = re.match(r'^\s+inet (addr:)?([\d\.]+)\s', line)
                    if m:
                        addrs.append(m.group(2))

                    m = re.match(r'^\sinet6 (addr: )?([\dabcdef\:]+)(/\d+)? '
                                 '.+[Gg]lobal$', line)
                    if m:
                        addrs.append(m.group(2))
                return addrs
        except OSError:
            pass

        return addrs

    def _file_systems_linux(self):
        logger.debug("Inspecting file systems.")
        fs = []
        (rc, out, err) = exec_command([which('df'), '--local', '-k'])
        lines = out.splitlines()
        # Remove header
        del lines[0]
        dev = None
        for line in lines:
            cols = line.decode('utf-8').split()
            # Skip rootfs which is redundant on Debian
            if cols[0] == 'rootfs':
                logger.debug("Ignoring rootfs mount point.")
                continue

            # Output of df can be multiline when the name of the
            # device is too large
            if len(cols) in (1, 6):
                dev = cols.pop(0)

            if not cols:
                # Multi-line output, skip to next line for next fields.
                continue

            # cols is now always [total, used, avail, use%, mount_point].
            total, used, _, _, mount_point = cols

            # Skip docker volumes.
            if dev in ('devtmpfs', 'overlay', 'shm', 'tmpfs'):
                logger.debug("Ignoring device %s as %s.", dev, mount_point)
                continue

            if dev.startswith('/dev/loop'):
                logger.debug("Ignoring loopback device %s.", dev)
                continue

            # Skip basic FHS directories.
            _, top_level_dir = mount_point.split('/', 2)[:2]
            if top_level_dir in ('dev', 'proc', 'run', 'sys'):
                logger.debug("Ignoring mount point %s.", mount_point)
                continue

            logger.debug("Found filesystem %s at %s.", dev, mount_point)
            fs.append({
                'mount_point': mount_point,
                'device': dev,
                'total': int(total) * 1024,
                'used': int(used) * 1024
            })
            dev = None
        return fs

    def mount_points(self):
        return [fs['mount_point'] for fs in self.file_systems()]

    def _find_mount_point_linux(self, path, mount_points):
        realpath = os.path.realpath(path)

        if not os.path.exists(realpath):
            return None

        # Get the parent dir when it is not a directory
        if not os.path.isdir(realpath):
            realpath = os.path.dirname(realpath)

        # Walk up parents directory
        while True:
            if realpath in mount_points or realpath == '/':
                return realpath

            realpath = os.path.dirname(realpath)


class PgInfo(Inventory):
    def __init__(self, db_conn):
        self.db_conn = db_conn

    def is_in_recovery(self):
        if self.db_conn.server_version >= 90000:
            return self.db_conn.queryscalar(
                "SELECT pg_is_in_recovery() AS standby;")
        return False

    def start_time(self):
        return self.db_conn.queryscalar("SELECT pg_postmaster_start_time();")

    def tablespaces(self, data_directory):
        # Grab the list of tablespaces
        if self.db_conn.server_version < 90200:
            q = """\
            SELECT spcname, spclocation, pg_tablespace_size(oid) AS size
            FROM pg_tablespace;
            """
        else:
            q = """\
            SELECT
              spcname,
              pg_tablespace_location(oid) AS spclocation,
              pg_tablespace_size(oid) AS size
            FROM pg_tablespace;
            """

        tablespaces = []
        sysinfo = SysInfo()
        fs = sysinfo.mount_points()
        for row in self.db_conn.query(q):
            # when spclocation is empty, replace with data_directory
            if row['spclocation'] is None:
                path = data_directory
            else:
                path = row['spclocation']

            tablespaces.append({
                'spcname': row['spcname'],
                'path': path,
                'mount_point': sysinfo.find_mount_point(path, fs),
                'size': row['size']
            })

    def databases(self):
        q = """\
        SELECT
          datname AS dbname, pg_encoding_to_char(encoding) AS encoding,
          pg_database_size(datname) AS size
        FROM pg_database WHERE datallowconn;
        """

        dbs = {}
        for r in self.db_conn.query(q):
            dbs[r['dbname']] = r
        return dbs
