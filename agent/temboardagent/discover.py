# Introspect Postgres instance, temBoard agent and system
#
# Discover is a stable set of properties identifying a running system.
#

import json
import logging
import os
import socket
import sys
from platform import machine, python_version
from multiprocessing import cpu_count

from .queries import QUERIES
from .toolkit.errors import UserError
from .toolkit.versions import (
    format_pq_version,
    read_distinfo,
    read_libpq_version,
)
from .tools import JSONEncoder
from .version import __version__


logger = logging.getLogger(__name__)


class Discover:
    def __init__(self, app):
        self.app = app
        self.path = self.app.config.temboard.home + '/discover.json'
        self.data = {}
        self.mtime = None

    def ensure_latest(self):
        if self.mtime != os.stat(self.path).st_mtime:
            logger.debug("Discover file changed.")
            return self.read()
        return self.data

    def read(self):
        logger.debug("Reading discover data from %s.", self.path)
        try:
            fo = open(self.path, 'r')
        except IOError as e:
            logger.debug("Failed to read manifest: %s.", e)
            return self.data

        with fo:
            try:
                data = json.load(fo)
            except json.JSONDecodeError as e:
                raise UserError("Malformed manifest: %s" % e)

            if not isinstance(data, dict):
                raise UserError("Malformed manifest: not a mapping")

        self.data.update(data)
        self.mtime = os.stat(self.path).st_mtime
        return self.data

    def write(self, fo=None):
        if fo is None:
            self.mtime = None

        with (fo or open(self.path, 'w')) as fo:
            json.dump(
                self.data,
                fo,
                indent="  ",
                sort_keys=True,
                cls=JSONEncoder,
            )
            fo.write("\n")  # Final new line.

        if self.mtime is None:  # if not sys.stdout.
            self.mtime = os.stat(self.path).st_mtime

    def refresh(self):
        logger.debug("Inspecting PostgreSQL instance and system.")
        d = self.data
        d.clear()

        d['postgres'] = {}
        d['system'] = {}
        d['temboard'] = {}

        d['temboard']['bin'] = sys.argv[0]
        d['temboard']['configfile'] = self.app.config.temboard.configfile
        d['temboard']['plugins'] = self.app.config.temboard.plugins

        d['system']['fqdn'] = self.app.config.temboard.hostname
        collect_versions(d)
        collect_cpu(d)
        collect_memory(d)
        collect_system(d)

        with self.app.postgres.connect() as conn:
            collect_postgres(d, conn)

        return self.data


def collect_cpu(data):
    s = data['system']
    s['cpu_count'] = cpu_count()

    with open('/proc/cpuinfo') as fo:
        for line in fo:
            if not line.startswith('model name\t'):
                continue
            _, _, model = line.partition("\t: ")
            s['cpu_model'] = model.rstrip()


def collect_memory(data):
    meminfo = {}
    with open('/proc/meminfo', 'r') as fo:
        for line in fo:
            if 'kB' not in line:
                continue
            field, value, kb = line.split()
            meminfo[field[:-1]] = int(value) * 1024

    s = data['system']
    s['memory'] = meminfo['MemTotal']
    s['swap'] = meminfo['SwapTotal']
    s['hugepage'] = meminfo['Hugepagesize']


def collect_postgres(data, conn):
    row = conn.queryone(QUERIES['discover'])
    data['postgres'].update(row)

    for row in conn.query(QUERIES['discover-settings']):
        t = row['vartype']
        v = row['setting']
        if 'integer' == t:
            v = int(v)
        elif 'bool' == t:
            v = 'on' == v

        u = row['unit']
        if u is None or 'B' == u:
            pass
        elif '8kB' == u:
            v = v * 8 * 1024
        else:
            raise ValueError("Unsupported unit %s" % u)
        data['postgres'][row['name']] = v


def collect_system(data):
    uname = os.uname()
    s = data['system']
    s['os'] = uname.sysname
    s['os_version'] = uname.release
    s['arch'] = machine()
    s['hostname'] = socket.gethostname()


def collect_versions(data):
    versions = inspect_versions()
    data['temboard'].update(dict(
        agent_version=versions['temboard'],
    ))

    for k in 'bottle', 'cryptography', 'libpq', 'psycopg2', 'python':
        data['temboard'][k + '_version'] = versions[k]

    data['temboard']['pythonbin'] = versions['pythonbin']
    dist = versions['distname'] + ' ' + versions['distversion']
    data['system']['distribution'] = dist


def inspect_versions():
    from bottle import __version__ as bottle_version
    from psycopg2 import __version__ as psycopg2_version
    from cryptography import __version__ as cryptography_version

    distinfos = read_distinfo()

    return dict(
        temboard=__version__,
        temboardbin=sys.argv[0],
        psycopg2=psycopg2_version,
        python=python_version(),
        pythonbin=sys.executable,
        bottle=bottle_version,
        distname=distinfos['NAME'],
        distversion=distinfos['VERSION'],
        libpq=format_pq_version(read_libpq_version()),
        cryptography=cryptography_version,
    )
