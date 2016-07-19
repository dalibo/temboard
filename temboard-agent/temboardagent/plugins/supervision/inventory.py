# -*- coding: utf-8 -*-
"""
The inventory contains support functions to discover the features of the host
(ex: OS, CPU info, MemInfo)

Currently, only Linux is supported.
"""

import os, re
import logging
import pwd
import socket, struct, fcntl
from supervision.utils import (exec_command, which, get_mount_points,
                             find_mount_point, check_fqdn, parse_linux_meminfo)
from temboardagent.spc import connector, error, get_pgpass




def get_cpuinfo(kernel):
    """
    Arguments:
        kernel (string): the type of OS. Currently, only Linux is supported

    Returns:
        dict: A dictionary containing cpu information with the following structure:

        .. code-block:: python

            {
                'cpu_frequency': frequency in Mhz (float)
                'cpu_count': Number of CPUs (int)
            }

    """
    cpus = []
    # TODO: implement for other OSes
    if kernel != 'Linux':
        return {}
    current_cpu = {}
    with open('/proc/cpuinfo') as f:
        for line in f.read().split("\n"):
            if ':' not in line:
                continue
            key, value = [part.strip() for part in line.split(':', 1)]
            if key == 'processor':
                current_cpu = {}
                cpus.append(current_cpu)
            current_cpu[key] = value
    if cpus:
        return {
            'cpu_count': len(cpus)
        }
    return {}


def get_meminfo(kernel):
    if kernel != 'Linux':
        return {}

    mem_values = parse_linux_meminfo()
    return {
        'memory_size': mem_values['MemTotal'],
        'swap_size': mem_values['SwapTotal']
    }


def get_ip_addresses(kernel):
    """Find the host's IP addresses."""
    if kernel != 'Linux':
        return {}

    addrs = []
    try:
        ip = which('ip')
        (rc, out, err) = exec_command([ip, "addr", "show"])
        if rc == 0:
            for line in out.decode('utf8').splitlines():
                m = re.match(r'^\s+inet ([\d\.]+)/\d+\s', line)
                if m:
                    addrs.append(m.group(1))

                m = re.match(r'^\sinet6 ([\dabcdef\:]+)/\d+ scope global', line)
                if m:
                    addrs.append(m.group(1))
            return addrs
    except OSError:
        pass

    try:
        ifconfig = which('ifconfig', ['/sbin'])
        (rc, out, err) = exec_command([ifconfig, "-a"])
        if rc == 0:
            for line in out.splitlines():
                m = re.match(r'^\s+inet (addr:)?([\d\.]+)\s', line)
                if m:
                    addrs.append(m.group(2))

                m = re.match(r'^\sinet6 (addr: )?([\dabcdef\:]+)(/\d+)? .+[Gg]lobal$', line)
                if m:
                    addrs.append(m.group(2))
            return addrs
    except OSError:
        pass

    return addrs

def get_file_systems(hostname):
    fs = []
    (rc, out, err) = exec_command([which('df'), '-k'])
    lines = out.splitlines()
    del lines[0] # Remove header
    dev = None
    for line in lines:
        cols = line.split()
        # Skip rootfs which is redundant on Debian
        if cols[0] == 'rootfs':
            continue

        # Output of df can be multiline when the name of the
        # device is too large
        if len(cols) == 1:
            dev = cols[0]
            continue
        if dev is not None:
            fs.append({
                'hostname': hostname,
                'mount_point': cols[4].decode('utf-8'),
                'device': dev.decode('utf-8'),
                'total': int(cols[0]) * 1024,
                'used': int(cols[1]) * 1024
            })
            dev = None
        else:
            # Single line output from df
            fs.append({
                'hostname': hostname,
                'mount_point': cols[5].decode('utf-8'),
                'device': cols[0].decode('utf-8'),
                'total': int(cols[1]) * 1024,
                'used': int(cols[2]) * 1024
            })
    return fs


def host_info(options):
    """Gather system information."""
    kernel, node, version, extra, arch = os.uname()

    if 'hostname' in options and options['hostname']:
        node = options['hostname']
    else:
        (hostname, _, _) = socket.gethostbyaddr(socket.gethostname())
        node = hostname.strip()

    if not check_fqdn(node):
        raise ValueError("Invalid FQDN: %s" % node)

    hostinfo = {
        "hostname": node,
        "os": kernel,
        "os_version": version,
        "cpu_arch": arch
    }
    hostinfo.update(get_cpuinfo(kernel))
    hostinfo.update(get_meminfo(kernel))
    hostinfo['ip_addresses'] = get_ip_addresses(kernel)
    hostinfo['filesystems'] = get_file_systems(node)

    if kernel == 'Linux':
        # TODO: split it into its own function
        # Distribution
        hostinfo["os_flavour"] = "Unknown"
        if os.path.exists("/etc/redhat-release"):
            try:
                fd = open("/etc/redhat-release")
                hostinfo["os_flavour"] = fd.readline().strip()
            except OSError as e:
                logging.error("[hostinfo] Could not read /etc/redhat-release: %s", str(e))
            else:
                fd.close()
        elif os.path.exists("/etc/debian_version"):
            try:
                fd = open("/etc/debian_version")
                hostinfo["os_flavour"] = "Debian " + fd.readline().strip()
            except OSError as e:
                logging.error("[hostinfo] Could not read /etc/debian_version: %s", str(e))
            else:
                fd.close()
    return hostinfo

def instance_info(conninfo, hostname):
    """Gather PostgreSQL instance information."""

    # Ensure we have all connection parameters
    if 'host' not in conninfo.keys():
        host = os.environ.get('PGHOST')
        if host is None:
            # Debian has a non-default unix_socket_directory
            if os.path.exists('/etc/debian_version'):
                host = '/var/run/postgresql'
            else:
                host = '/tmp'
    else:
        host = conninfo['host']

    if 'port' not in conninfo.keys():
        port = os.environ.get('PGPORT')
        if port is None:
            port = 5432
    else:
        port = conninfo['port']

    if 'user' not in conninfo.keys():
        user = os.environ.get('PGUSER')
        if user is None:
            user = pwd.getpwuid(os.geteuid()).pw_name
    else:
        user = conninfo['user']

    if 'database' not in conninfo.keys():
        database = os.environ.get('PGDATABASE')
        if database is None:
            database = user
    else:
        database = conninfo['database']

    if 'password' not in conninfo.keys():
        password = os.environ.get('PGPASSWORD')
        if password is None:
            # pgpass file handling
            try:
                pgpa_file = os.environ.get('PGPASSFILE')
                for (pgpa_h, pgpa_p, pgpa_d, pgpa_u, pgpa_pwd) in \
                    get_pgpass(pgpa_file):
                    if (pgpa_h == host or pgpa_h == '*') and \
                        (pgpa_p == port or pgpa_p == '*') and \
                        (pgpa_u == user or pgpa_u == '*') and \
                        (pgpa_d == database or pgpa_d == '*'):
                        password = pgpa_pwd
                        continue
            except Exception as err:
                pass
    else:
        password = conninfo['password']


    instance_info = {
        'hostname': hostname,
        'instance': conninfo['instance'],
        'local_name': conninfo.get('local_name', conninfo['instance']),
        'available': True,
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database,
    }

    # Try the connection
    conn = connector(host, port, user, password, database)
    try:
        conn.connect()
        # Gather the info while where are connected
        instance_info['version_num'] = conn.get_pg_version()

        conn.execute("SELECT setting FROM pg_settings WHERE name = 'server_version';")
        instance_info['version'] = list(conn.get_rows())[0]['setting']

        conn.execute("SELECT setting FROM pg_settings WHERE name = 'data_directory';")
        instance_info['data_directory'] = list(conn.get_rows())[0]['setting']

        # hot standby is available from 9.0
        instance_info['standby'] = False
        if instance_info['version_num'] >= 90000:
            conn.execute("SELECT pg_is_in_recovery() AS standby;")
            if list(conn.get_rows())[0]['standby'] == 't':
                instance_info['standby'] = True

        # Grab the list of tablespaces
        if instance_info['version_num'] < 90200:
            conn.execute("SELECT spcname, spclocation FROM pg_tablespace;")
        else:
            conn.execute("SELECT spcname, pg_tablespace_location(oid) AS spclocation FROM pg_tablespace;")

        instance_info['tablespaces'] = []
        fs = get_mount_points()
        for row in conn.get_rows():
            # when spclocation is empty, replace with data_directory
            if row['spclocation'] is None:
                path = instance_info['data_directory']
            else:
                path = row['spclocation']

            # Include hostname and port to ease processing by ther server
            instance_info['tablespaces'].append({
                'hostname': hostname,
                'port': instance_info['port'],
                'spcname': row['spcname'],
                'path': path,
                'mount_point': find_mount_point(path, fs)
            })

        # When the user has not given a dbnames list or '*' in the
        # configuration file, we must get the list of databases. Since
        # we have a working connection, let's do it now.
        conn.execute("""
        SELECT datname AS dbname, pg_encoding_to_char(encoding) AS encoding
        FROM pg_database
        WHERE datallowconn;
        """)

        dbs = {}
        for r in conn.get_rows():
            r['hostname'] = hostname
            r['port'] = instance_info['port']
            dbs[r['dbname']] = r

        instance_info['dbnames'] = []
        for db in conninfo['dbnames']:
            if db == '*':
                instance_info['dbnames'] = dbs.values()
                break
            if db in dbs.keys():
                instance_info['dbnames'].append(dbs[db])
        conn.close()

        # Now that we have the data_directory, find the owner
        try:
            statinfo = os.stat(instance_info['data_directory'])
            instance_info['sysuser'] = pwd.getpwuid(statinfo.st_uid).pw_name
        except OSError as e:
            logging.warning("Unable to get the owner of PGDATA: %s", str(e))
            instance_info['sysuser'] = None

    except error as e:
        logging.warning("Unable to gather information for cluster \"%s\"", conninfo['instance'])
        instance_info['available'] = False

    return instance_info
