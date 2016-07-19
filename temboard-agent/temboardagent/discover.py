import re
import socket
from ganesh.command import exec_command

def get_pg_version(conn):
    query = "SELECT version() AS version"
    conn.execute(query)
    return list(conn.get_rows())[0]['version']

def get_pg_port(conn):
    query = "SELECT setting FROM pg_settings WHERE name = 'port'"
    conn.execute(query)
    return int(list(conn.get_rows())[0]['setting'])

def get_pg_data(conn):
    query = "SELECT setting FROM pg_settings WHERE name = 'data_directory'"
    conn.execute(query)
    return list(conn.get_rows())[0]['setting']

def get_linux_memory_size():
    mem_total = 0
    pattern_line_meminfo = re.compile('^([^:]+):\s+([0-9]+) kB$')
    with open('/proc/meminfo', 'r') as fd:
        for line in fd.readlines():
            m = pattern_line_meminfo.match(line)
            if m:
                key = m.group(1)
                value = m.group(2)
            if key == "MemTotal":
                mem_total = int(value)
                return mem_total * 1024

def get_unix_os_version():
    (returncode, stdout, stderrout) = exec_command(['/bin/uname', '-sri'])
    if returncode == 0:
        return stdout.strip()

def get_memory_size():
    os_version = get_unix_os_version()
    if os_version and os_version.startswith('Linux'):
        return get_linux_memory_size()

def get_linux_hostname():
    (hostname, _, _) = socket.gethostbyaddr(socket.gethostname())
    return hostname.strip()

def get_hostname():
    os_version = get_unix_os_version()
    if os_version and os_version.startswith('Linux'):
        return get_linux_hostname()

def get_n_cpu():
    from multiprocessing import cpu_count
    return cpu_count()
