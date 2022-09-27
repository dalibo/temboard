# Introspect Postgres instance, temBoard agent and system
#
# Discover is a stable set of properties identifying a running system. temBoard
# computes an ETag from discover data to ease change detection.
#
# Discover data is cached in a discover.json file. temBoard refreshes this file
# in two cases : start of agent, connection lost.
#

import hashlib
import json
import logging
import os
import socket
import sys
from platform import machine, python_version
from multiprocessing import cpu_count

from .core import workers
from .queries import QUERIES
from .toolkit.errors import UserError
from .toolkit.versions import (
    format_pq_version,
    read_distinfo,
    read_libpq_version,
)
from .tools import noop_manager
from .version import __version__


logger = logging.getLogger(__name__)


class Discover:
    def __init__(self, app):
        self.app = app
        self.path = self.app.config.temboard.home + '/discover.json'
        self.data = dict(postgres={}, system={}, temboard={})
        self.json = None  # bytes
        self.etag = None
        self.file_etag = None
        self.mtime = None
        self.inhibit_observer = False

    def connection_lost(self):
        if self.inhibit_observer:
            return
        # Callback for postgres.ConnectionPool connection lost event.
        logger.info("Queueing discover refresh.")
        discover.defer(self.app)

    def ensure_latest(self):
        if self.mtime != os.stat(self.path).st_mtime:
            logger.debug("Discover file changed.")
            return self.read()
        return self.data

    def read(self):
        logger.debug("Reading discover data from %s.", self.path)
        try:
            fo = open(self.path, 'rb')
        except IOError as e:
            logger.debug("Failed to read manifest: %s.", e)
            return self.data

        with fo:
            self.json = fo.read()

        self.etag = self.file_etag = compute_etag(self.json)

        try:
            data = json.loads(self.json.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise UserError("Malformed manifest: %s" % e)

        if not isinstance(data, dict):
            raise UserError("Malformed manifest: not a mapping")

        self.data.update(data)
        self.mtime = os.stat(self.path).st_mtime
        return self.data

    def write(self, fo=None):
        if fo is None:
            if self.etag == self.file_etag:
                logger.debug("Discover file up to date.")
                return
            self.mtime = None

        with (fo or open(self.path, 'w')) as fo:
            fo.write(self.json.decode('utf-8'))

        if self.mtime is None:  # if not sys.stdout.
            logger.debug("Wrote discover.json with ETag %s.", self.etag)
            self.mtime = os.stat(self.path).st_mtime
            self.file_etag = self.etag

    def refresh(self, conn=None):
        logger.debug("Inspecting temBoard and system.")
        d = self.data
        old_postgres = self.data.get('postgres', {})
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

        try:
            mgr = noop_manager(conn) if conn else self.app.postgres.connect()
        except Exception as e:
            logger.error("Failed to collect Postgres data: %s", e)
            d['postgres'] = old_postgres
        else:
            with mgr as conn:
                logger.debug("Inspecting Postgres instance.")
                collect_postgres(d, conn)

        # Build JSON to compute ETag.
        json_text = json.dumps(
            self.data,
            indent="  ",
            sort_keys=True,
        ) + "\n"
        self.json = json_text.encode('utf-8')
        self.etag = compute_etag(self.json)

        if self.etag != self.file_etag:
            logger.info("Instance discover updated.")
        else:
            logger.debug("Instance discover has not changed.")

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
        distversion=distinfos.get('VERSION', 'n/a'),
        libpq=format_pq_version(read_libpq_version()),
        cryptography=cryptography_version,
    )


def compute_etag(data):
    h = hashlib.new('sha256')
    h.update(data)
    return h.hexdigest()


@workers.register(pool_size=1)
def discover(app):
    """ Refresh discover data. """
    app.discover.ensure_latest()
    app.discover.inhibit_observer = True
    app.discover.refresh()
    app.discover.inhibit_observer = False
    app.discover.write()
