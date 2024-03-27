import logging
import re
import os
import time
import json
from contextlib import closing

import psycopg2
from psycopg2.extensions import parse_dsn
from psycopg2.extras import PhysicalReplicationConnection

from ...inventory import SysInfo
from ...plugins.maintenance.functions import INDEX_BTREE_BLOAT_SQL
from ...toolkit.utils import utcnow

from . import db


logger = logging.getLogger(__package__)


def load_probes(options, home):
    """Give a list of probe objects, ready to run."""

    # All probes classes names start with "probe_", search for
    # classes and get an object
    probes = []
    r = re.compile(r'^probe_(\w+)$')
    for c in globals().keys():
        m = r.search(c)
        if m is not None \
           and issubclass(globals()[c], Probe) \
           and (m.group(1) in options['probes'] or '*' in options['probes']):
            o = eval(c + "(options)")
            o.set_home(home)
            probes.append(o)
            logger.debug("Loaded probe: %s.", o.get_name())

    return probes


def run_probes(probes, pool, instances, delta=True):
    """Execute the probes."""

    now = utcnow()
    logger.info("Running probes at %s.", now.isoformat())
    # Output is a mapping of probe names with lists. Each probe returns
    # a list of dicts(metric -> value).
    output = {}

    for p in probes:
        out = []
        if delta is False:
            p.delta_key = None
            p.delta_columns = None

        if p.level == 'host':
            if not p.check():
                continue
            logger.info("Running host probe %s.", p.get_name())
            try:
                out = p.run()
            except Exception as e:
                logger.error("Probe failure: %s", e)
                continue

        else:
            if p.level not in ('instance', 'database'):
                raise Exception("Unknown probe level: %s", p.level)

            i, = instances  # We are now mono-instance
            if not i['available']:
                continue

            if not p.check(i['version_num']):
                logger.warning(
                    "Unsupported PostgreSQL version for probe %s.",
                    p.get_name())
                continue

            logger.info("Running %s probe %s.", p.level, p.get_name())
            if p.level == 'instance':
                dbnames = [i['database']]
            else:
                dbnames = [db['dbname'] for db in i['dbnames']]

            for dbname in dbnames:
                conninfo = dict(i, dbname=dbname)
                try:
                    out += p.run(pool.getconn(dbname=dbname), conninfo)
                except Exception as e:
                    logger.error("Probe failure: %s", e)
                    raise
                    continue

        for record in out:
            record['datetime'] = now
        output[p.get_name()] = out

    logger.info("Finished probes run.")
    return output


def parse_primary_conninfo(pci):
    # Parse primary_conninfo string picked up from recovery.conf file
    m = re.match(r'.*primary_conninfo\s*=\s*\'(.*)\'[^\']*$', pci)
    if not m:
        raise Exception("Unable to parse primary_conninfo.")

    # Unquote string. When coming from recovery.conf, single quotes can be
    # doubled or escaped with a backslash
    c = m.group(1).replace("''", "'")
    c = c.replace("\\'", "'")

    # Keep only compat parameters because we may be bound to an old libpq.
    well_known_params = [
        p for p in c.split() if (
            p.startswith('user') or
            p.startswith('password') or
            p.startswith('host') or
            p.startswith('port') or
            p.startswith('sslmode')
        )
    ]

    c = ' '.join(well_known_params)

    return c


def get_primary_conninfo(conn):
    # Read and parse primary_conninfo from recovery.conf file if any or from
    # pg_settings if PG version is upper or equal to 12.
    # It returns a tuple: (host, port, user, password)

    # Check if we are in recovery mode *and* recovery file exists
    if conn.server_version < 120000:
        # Note: won't work with PG12
        query = """\
        SELECT (pg_is_in_recovery() AND (
          length(
            coalesce(
              pg_stat_file('recovery.conf', true)::TEXT, ''::TEXT
            )
          ) > 0
        )) AS is_in_recovery
        """
    else:
        query = """\
        SELECT (pg_is_in_recovery() AND (
            length(
            coalesce(
                pg_stat_file('standby.signal', true)::TEXT, ''::TEXT
            )
            ) > 0
        )) AS is_in_recovery
        """
    is_in_recovery = conn.queryscalar(query)
    if not is_in_recovery:
        raise Exception("Instance not in recovery or recovery file is "
                        "missing.")

    if conn.server_version < 120000:
        # Fetch primary_conninfo from recovery.conf file
        # Note: won't work with PG12
        query = """\
        SELECT l FROM unnest(
          string_to_array(
            pg_read_file('recovery.conf'), E'\\n'
          )
        ) AS l
        WHERE l LIKE '%primary\\_conninfo%'
        """
    else:
        query = """\
        SELECT 'primary_conninfo='||quote_literal(setting) AS l
            FROM pg_settings WHERE name='primary_conninfo'
        """
    r = list(conn.query(query))
    if len(r) == 0:
        raise Exception("Unable to get primary_conninfo.")
    pci = r[0]['l']
    # Parse and return primary_conninfo
    return parse_primary_conninfo(pci)


class Probe:
    """Base class for all plugins."""
    # At which level the information is gathered: host, instance or db
    level = None
    # Optionnal name of the probe
    name = None
    # Previous measures used for compute delta
    last_measure = {}
    last_measure_time = {}
    home = None

    def __init__(self, options):
        pass

    def check(self):
        """Check if the plugin can run on the target."""
        pass

    def run(self):
        """Returns the result."""
        pass

    def set_home(self, home):
        self.home = home

    def get_name(self):
        """Computes the name of the probe."""
        # Let the plugin overwrite the name
        if self.name is not None:
            return self.name

        # Compute the name from the class of the plugin
        m = re.search(r'^probe_(\w+)$', self.__class__.__name__.lower())
        if m is not None:
            return m.group(1)

        logger.error("Could not get the name of the probe")
        return None

    def get_last_measure(self, key):
        row = db.get_last_measure(
            self.home,
            'monitoring.db',
            key
        )
        if row:
            return dict(time=row[0], data=json.loads(row[1]))

    def upsert_last_measure(self, time, key, data):
        db.upsert_last_measure(
            self.home,
            'monitoring.db',
            time,
            key,
            data
        )

    def delta(self, key, current_values):
        """
        Compute a delta between measures of two runs.

        Args:
            key (str): identify the values
            current_values (dict): mapping of latest measures

        Returns:
            a tuple of the time interval of the delta in seconds and a
            dict a delta with the same keys as the input.
        """
        current_time = time.time()
        store_key = self.get_name() + key
        last_measure = self.get_last_measure(store_key)
        delta = dict(current=current_values)
        delta_value = None
        # Compute deltas and update last_* variables
        try:
            if last_measure:
                delta['measure_interval'] = current_time - last_measure['time']

                for k in current_values.keys():
                    delta_value = current_values[k] - \
                        last_measure['data'][k]
                    if delta_value < 0:
                        raise Exception('Negative delta value.')
                    delta[k] = delta_value
        except Exception as e:
            logger.debug("Failed to compute delta metric: %s", e)

        # Update/insert last measure for next delta calculation
        self.upsert_last_measure(
            current_time,
            store_key,
            current_values
        )

        return delta

    def __repr__(self):
        return self.get_name()


class HostProbe(Probe):
    """
        system probe base class
    """
    level = 'host'
    system = None  # kernel name from os.uname()[0]
    min_version = None
    max_version = None

    def check(self):
        """Check if the probe can run on this system."""
        if self.system is not None:
            if self.system != os.uname()[0]:
                return False

        version = [int(x) for x
                   in re.sub(r'[-_+].*$', '', os.uname()[2]).split('.')]
        if self.min_version is not None:
            if version[0:len(self.min_version)] < self.min_version:
                return False

        if self.max_version is not None:
            if version[0:len(self.max_version)] > self.max_version:
                return False

        return True


class SqlProbe(Probe):
    """
        postgres probe base class
    """
    min_version = None
    max_version = None
    sql = None
    no_standby = False

    # Delta columns is a list of columns in the output of the query on
    # which delta are computed between to runs. When is it set, a new
    # key is added with the time interval of the delta named with
    # measure_interval. delta_key a column used as unique key to
    # compute delta on multiline output.
    delta_columns = None
    delta_key = None
    timeout = False

    def check(self, version=None):
        """Check if the plugin can run on the target version of PostgreSQL."""
        if version is None:
            return False

        if self.min_version is not None:
            if version < self.min_version:
                return False

        if self.max_version is not None:
            if version > self.max_version:
                return False

        return True

    def run_sql(self, conn, conninfo, sql):
        """Get the result of the SQL query"""
        if sql is None:
            return []

        database = conninfo['dbname']

        output = []
        try:
            if self.timeout:
                conn.execute(
                    "SET statement_timeout = '%ss';", (self.timeout,))

            cluster_name = conninfo['instance'].replace('/', '')
            sql = f"-- probe {self}\n{sql}"
            for r in conn.query(sql):
                # Compute delta if the probe needs that
                if self.delta_columns is not None:
                    to_delta = {}

                    for k in self.delta_columns:
                        if k in r.keys():
                            to_delta[k] = r.pop(k)

                    # Create the store key for the delta
                    if self.delta_key is not None:
                        key = cluster_name + database + r[self.delta_key]
                    else:
                        key = cluster_name + database

                    # Calculate and add delta.
                    r.update(self.delta(key, to_delta))

                output.append(r)
        except Exception as e:
            logger.error(
                "Unable to run probe \"%s\" on \"%s\" on database \"%s\": %s",
                self.get_name(), conninfo['instance'], database, e,
                exc_info=True,
            )
        return output

    def run(self, conn, conninfo):
        """Execute the query depending on the level configured."""
        if self.no_standby and conninfo['standby']:
            return []

        return self.run_sql(conn, conninfo, self.sql)


class probe_sessions(SqlProbe):
    level = 'instance'

    def check(self, version):
        if not super().check(version):
            return False

        if version < 90200:
            self.sql = """select
  d.datname as dbname,
  coalesce(sum((current_query not in ('<IDLE>','<IDLE> in transaction') and not waiting)::integer), 0) as active,
  coalesce(sum(waiting::integer), 0) as waiting,
  coalesce(sum((current_query='<IDLE>')::integer), 0) as idle,
  coalesce(sum((current_query='<IDLE> in transaction')::integer), 0) as idle_in_xact,
  0 as idle_in_xact_aborted,
  coalesce(sum((current_query='<FASTPATH> function call')::integer), 0) as fastpath,
  coalesce(sum((current_query='<command string not enabled>')::integer), 0) as disabled,
  coalesce(sum((current_query='<insufficient privilege>')::integer), 0) as no_priv
from pg_database d
  left join pg_stat_activity a on (d.oid = a.datid)
where d.datallowconn
group by d.datname"""  # noqa
        elif version >= 90200 and version < 90600:
            self.sql = """select
  d.datname as dbname,
  coalesce(sum((state = 'active' and not waiting)::integer), 0) as active,
  coalesce(sum((state = 'active' and waiting)::integer), 0) as waiting,
  coalesce(sum((state = 'idle')::integer), 0) as idle,
  coalesce(sum((state = 'idle in transaction')::integer), 0) as idle_in_xact,
  coalesce(sum((state = 'idle in transaction (aborted)')::integer), 0) as idle_in_xact_aborted,
  coalesce(sum((state = 'fastpath function call')::integer), 0) as fastpath,
  coalesce(sum((state = 'disabled')::integer), 0) as disabled,
  coalesce(sum((query = '<insufficient privilege>')::integer), 0) as no_priv
from pg_database d
  left join pg_stat_activity a on (d.oid = a.datid)
where d.datallowconn
group by d.datname"""  # noqa
        elif version >= 90600:
            self.sql = """select
  d.datname as dbname,
  coalesce(sum((state = 'active' and wait_event_type IS DISTINCT FROM 'Lock')::integer), 0) as active,
  coalesce(sum((state = 'active' and wait_event_type IS NOT DISTINCT FROM 'Lock')::integer), 0) as waiting,
  coalesce(sum((state = 'idle')::integer), 0) as idle,
  coalesce(sum((state = 'idle in transaction')::integer), 0) as idle_in_xact,
  coalesce(sum((state = 'idle in transaction (aborted)')::integer), 0) as idle_in_xact_aborted,
  coalesce(sum((state = 'fastpath function call')::integer), 0) as fastpath,
  coalesce(sum((state = 'disabled')::integer), 0) as disabled,
  coalesce(sum((query = '<insufficient privilege>')::integer), 0) as no_priv
from pg_database d
  left join pg_stat_activity a on (d.oid = a.datid)
where d.datallowconn
group by d.datname"""  # noqa

        return True


class probe_xacts(SqlProbe):
    level = 'instance'
    min_version = 70400
    sql = """select
  s.datname as dbname,
  xact_commit as n_commit,
  xact_rollback as n_rollback
from pg_stat_database s
  join pg_database d on (d.oid = s.datid)
where d.datallowconn"""
    delta_columns = ['n_commit', 'n_rollback']
    delta_key = 'dbname'


class probe_locks(SqlProbe):
    level = 'instance'
    sql = """select
  d.datname as dbname,
  coalesce(sum((mode = 'AccessShareLock' and granted)::integer), 0) as access_share,
  coalesce(sum((mode = 'AccessShareLock' and not granted)::integer), 0) as waiting_access_share,
  coalesce(sum((mode = 'RowShareLock' and granted)::integer), 0) as row_share,
  coalesce(sum((mode = 'RowShareLock' and not granted)::integer), 0) as waiting_row_share,
  coalesce(sum((mode = 'RowExclusiveLock' and granted)::integer), 0) as row_exclusive,
  coalesce(sum((mode = 'RowExclusiveLock' and not granted)::integer), 0) as waiting_row_exclusive,
  coalesce(sum((mode = 'ShareUpdateExclusiveLock' and granted)::integer), 0) as share_update_exclusive,
  coalesce(sum((mode = 'ShareUpdateExclusiveLock' and not granted)::integer), 0) as waiting_share_update_exclusive,
  coalesce(sum((mode = 'ShareLock' and granted)::integer), 0) as share,
  coalesce(sum((mode = 'ShareLock' and not granted)::integer), 0) as waiting_share,
  coalesce(sum((mode = 'ShareRowExclusiveLock' and granted)::integer), 0) as share_row_exclusive,
  coalesce(sum((mode = 'ShareRowExclusiveLock' and not granted)::integer), 0) as waiting_share_row_exclusive,
  coalesce(sum((mode = 'ExclusiveLock' and granted)::integer), 0) as exclusive,
  coalesce(sum((mode = 'ExclusiveLock' and not granted)::integer), 0) as waiting_exclusive,
  coalesce(sum((mode = 'AccessExclusiveLock' and granted)::integer), 0) as access_exclusive,
  coalesce(sum((mode = 'AccessExclusiveLock' and not granted)::integer), 0) as waiting_access_exclusive,
  coalesce(sum((mode = 'SIReadLock' and granted)::integer), 0) as siread
from pg_database d
  left join pg_locks l on (l.database = d.oid)
where d.datallowconn
group by d.datname"""  # noqa


class probe_blocks(SqlProbe):
    level = 'instance'
    sql = """select
  s.datname as dbname,
  blks_read,
  blks_hit,
  coalesce(blks_hit::float*100/nullif(blks_read+blks_hit, 0), 0) as hitmiss_ratio
from pg_stat_database s
  join pg_database d on (d.oid = s.datid)
where d.datallowconn"""  # noqa
    delta_columns = ['blks_read', 'blks_hit']
    delta_key = 'dbname'


class probe_bgwriter(SqlProbe):
    level = 'instance'
    min_version = 80300
    sql = """select * from pg_stat_bgwriter"""
    delta_columns = [
        'checkpoints_timed', 'checkpoints_req', 'checkpoint_write_time',
        'checkpoint_sync_time', 'buffers_checkpoint', 'buffers_clean',
        'maxwritten_clean', 'buffers_backend', 'buffers_backend_fsync',
        'buffers_alloc'
    ]


class probe_db_size(SqlProbe):
    level = 'instance'
    sql = """select
  datname as dbname,
  pg_database_size(oid) as size
from pg_database
where datallowconn"""


class probe_tblspc_size(SqlProbe):
    level = 'instance'
    sql = """select
  spcname,
  pg_tablespace_size(oid) as size
from pg_tablespace"""


class probe_filesystems_size(HostProbe):
    system = 'Linux'

    def run(self):
        return SysInfo().file_systems()


class probe_cpu(HostProbe):
    system = 'Linux'
    hz = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

    def run(self):
        to_delta = {}
        stat = open('/proc/stat')
        for line in stat:
            cols = line.split()
            if len(cols) == 0:
                continue
            if cols[0] == 'cpu':
                # Convert values to int then in milliseconds,
                to_delta = {
                    'time_user': ((int(cols[1]) + int(cols[2])) * 1000 /
                                  self.hz),
                    'time_system': (int(cols[3]) + int(cols[6]) +
                                    int(cols[7])) * 1000 / self.hz,
                    'time_idle': int(cols[4]) * 1000 / self.hz,
                    'time_iowait': int(cols[5]) * 1000 / self.hz,
                    'time_steal': int(cols[8]) * 1000 / self.hz
                }
        stat.close()

        # Compute deltas for values of /proc/stat since boot time
        metrics = self.delta('global', to_delta)
        metrics['cpu'] = 'global'

        return [metrics]


class probe_process(HostProbe):
    system = 'Linux'

    def run(self):
        metrics = {}
        # Process information is partly stored in /proc/stat, ctxt and
        # processes are ever incresing counters, compute deltas on
        # them.
        to_delta = {}
        stat = open('/proc/stat')
        for line in stat:
            cols = line.split()
            if len(cols) == 0:
                continue
            if cols[0] == 'ctxt':
                to_delta['context_switches'] = int(cols[1])
            if cols[0] == 'processes':
                to_delta['forks'] = int(cols[1])
            if cols[0] == 'procs_running':
                metrics['procs_running'] = int(cols[1])
            if cols[0] == 'procs_blocked':
                metrics['procs_blocked'] = int(cols[1])
        stat.close()

        # Total number of process is stored in /proc/loadavg
        load = open('/proc/loadavg')
        m = re.match(r'.*/(\d+) ', load.readline())
        load.close()
        if m:
            metrics['procs_total'] = m.group(1)
        else:
            metrics['procs_total'] = 0

        # Compute deltas for values of /proc/stat since boot time
        metrics.update(self.delta('key', to_delta))
        return [metrics]


class probe_memory(HostProbe):
    system = 'Linux'

    def run(self):
        sysinfo = SysInfo()
        meminfo = sysinfo.mem_info()

        return [{
            'mem_total': meminfo['MemTotal'],
            'mem_used': meminfo['MemTotal'] - meminfo['MemFree'],
            'mem_free': meminfo['MemFree'],
            'mem_buffers': meminfo['Buffers'],
            'mem_cached': meminfo['Cached'],
            'swap_total': meminfo['SwapTotal'],
            'swap_used': meminfo['SwapTotal'] - meminfo['SwapFree']
        }]


class probe_loadavg(HostProbe):
    system = 'Linux'

    def run(self):
        loadavg = open('/proc/loadavg')
        cols = loadavg.readline().split()
        loadavg.close()
        return [{
            'load1': cols[0],
            'load5': cols[1],
            'load15': cols[2]
        }]


class probe_wal_files(SqlProbe):
    level = 'instance'
    min_version = 80200

    def run(self, conn, conninfo):
        version = conn.server_version

        if conninfo['standby']:
            return []

        metric = {}
        if version < 100000:
            sql = """
            SELECT count(s.f) AS total,
                   sum((pg_stat_file('pg_xlog/'||s.f)).size) AS total_size,
                   pg_current_xlog_location() as current_location
            FROM pg_ls_dir('pg_xlog') AS s(f)
            WHERE f ~ E'^[0-9A-F]{24}$'
            """
        else:
            sql = """
            SELECT count(s.f) AS total,
                   sum((pg_stat_file('pg_wal/'||s.f)).size) AS total_size,
                   pg_current_wal_lsn() as current_location
            FROM pg_ls_dir('pg_wal') AS s(f)
            WHERE f ~ E'^[0-9A-F]{24}$'
            """
        rows = self.run_sql(conn, conninfo, sql)

        metric['total'] = rows[0]['total']
        metric['total_size'] = rows[0]['total_size']
        metric['current_location'] = rows[0]['current_location']

        if version < 100000:
            sql = r"""
            SELECT count(s.f) AS archive_ready
            FROM pg_ls_dir('pg_xlog/archive_status') AS s(f)
            WHERE f ~ E'\.ready$'
            """  # noqa W605
        else:
            sql = r"""
            SELECT count(s.f) AS archive_ready
            FROM pg_ls_dir('pg_wal/archive_status') AS s(f)
            WHERE f ~ E'\.ready$'
            """  # noqa W605
        rows = self.run_sql(conn, conninfo, sql)

        metric['archive_ready'] = rows[0]['archive_ready']

        # Calcutate the written size by using the delta between the
        # position between to runs. The current xlog location must be
        # converted to an number first
        m = re.match(r'^([0-9A-F]+)/([0-9A-F]+)$', metric['current_location'])
        if m:
            current = int("0xff000000", 0) * \
                int("0x" + m.group(1), 0) + int("0x" + m.group(2), 0)
        else:
            logger.error("Unable to convert xlog location to a number")
            return []

        metric.update(self.delta(
            conninfo['instance'].replace('/', ''),
            {'written_size': current},
        ))
        return [metric]


class probe_replication_lag(SqlProbe):
    # Streaming replication lag probe, in bytes
    #
    # The instance is in recovery mode ?
    # + recovery.conf file exists ?
    # + recovery.conf contains primary_conninfo ?
    # + get primary node's current wal position with IDENTIFY_SYSTEM
    #   through streaming repl. protocol
    # + return primary wal position and current replay diff.
    level = 'instance'
    min_version = 90000

    def run(self, conn, conninfo):
        if not conninfo['standby']:
            return []

        try:
            # Get primary parameters from primary_conninfo
            dsn = get_primary_conninfo(conn)

            # Let's fetch primary current wal position with IDENTIFY_SYSTEM
            # through streaming replication protocol.
            with closing(psycopg2.connect(
                dsn, connection_factory=PhysicalReplicationConnection
            )) as p_conn:
                with p_conn.cursor() as p_cur:
                    p_cur.execute("IDENTIFY_SYSTEM")
                    rows = p_cur.fetchall()

                    if len(rows) == 0:
                        return []
                    xlogpos = rows[0][2]

            # Proceed with LSN diff
            if conn.server_version >= 100000:
                # Use pg_wal_lsn_diff(pg_lsn, pg_lsn)
                rows = conn.query("""\
                SELECT pg_wal_lsn_diff(
                    '{xlogpos}'::pg_lsn,
                    pg_last_wal_replay_lsn()
                ) AS lsn_diff
                """.format(xlogpos=xlogpos))
            elif conn.server_version >= 90500:
                # Use pg_xlog_lsn_diff(pg_lsn, pg_lsn)
                rows = conn.query("""\
                SELECT pg_xlog_location_diff(
                    '{xlogpos}'::pg_lsn,
                    pg_last_xlog_replay_location()
                ) AS lsn_diff
                """.format(xlogpos=xlogpos))
            else:
                # Use pg_xlog_lsn_diff(TEXT, TEXT)
                rows = conn.query("""\
                SELECT pg_xlog_location_diff(
                    '{xlogpos}'::TEXT,
                    pg_last_xlog_replay_location()::TEXT
                ) AS lsn_diff
                """.format(xlogpos=xlogpos))
            r = list(rows)
            if len(r) == 0:
                return []
            return [{'lag': int(r[0]['lsn_diff'])}]

        except Exception as e:
            logger.exception(str(e))
            return []


class probe_temp_files_size_delta(SqlProbe):
    # Temporary files probe
    level = 'instance'
    sql = """SELECT
  s.datname AS dbname,
  temp_bytes AS size
FROM pg_stat_database s
JOIN pg_database d ON (d.oid = s.datid)
WHERE d.datallowconn"""  # noqa
    delta_columns = ['size']
    delta_key = 'dbname'


class probe_replication_connection(SqlProbe):
    # Check if the instance is connected to streaming replication according to
    # primary_conninfo from recovery.conf file.
    level = 'instance'
    min_version = 96000

    def run(self, conn, conninfo):
        if not conninfo['standby']:
            return []

        try:
            # Get primary parameters from primary_conninfo
            dsn = parse_dsn(get_primary_conninfo(conn))
            p_host = dsn['host']

            # pg_stat_wal_receiver lookup
            rows = conn.query("""\
            SELECT '{p_host}' AS upstream,
            CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS connected
            FROM pg_stat_wal_receiver
            WHERE status='streaming' AND
                    conninfo LIKE '%host={p_host}%'
            """.format(p_host=p_host))
            return list(rows)
        except Exception as e:
            logger.exception(str(e))
            return []


class probe_heap_bloat(SqlProbe):
    # Heap bloat estimation probe
    # Query coming from https://github.com/ioguix/pgsql-bloat-estimation/
    level = 'database'
    sql = """
SELECT current_database() AS dbname,
  SUM(bloat_size)::FLOAT/SUM(bs*tblpages)::FLOAT*100 AS ratio
FROM (
  SELECT
  CASE WHEN tblpages - est_tblpages_ff > 0 THEN (tblpages-est_tblpages_ff)*bs ELSE 0 END AS bloat_size,
  bs, tblpages
  FROM (
    SELECT
      ceil( reltuples / ( (bs-page_hdr)*fillfactor/(tpl_size*100) ) ) + ceil( toasttuples / 4 ) AS est_tblpages_ff,
      tblpages, bs
    FROM (
      SELECT
        ( 4 + tpl_hdr_size + tpl_data_size + (2*ma)
          - CASE WHEN tpl_hdr_size%ma = 0 THEN ma ELSE tpl_hdr_size%ma END
          - CASE WHEN ceil(tpl_data_size)::int%ma = 0 THEN ma ELSE ceil(tpl_data_size)::int%ma END
        ) AS tpl_size, bs - page_hdr AS size_per_block, (heappages + toastpages) AS tblpages, heappages,
        toastpages, reltuples, toasttuples, bs, page_hdr, tblid, schemaname, tblname, fillfactor
      FROM (
        SELECT
          tbl.oid AS tblid, ns.nspname AS schemaname, tbl.relname AS tblname,
          tbl.reltuples, tbl.relpages AS heappages, coalesce(toast.relpages, 0) AS toastpages,
          coalesce(toast.reltuples, 0) AS toasttuples,
          coalesce(substring(
            array_to_string(tbl.reloptions, ' ')
            FROM 'fillfactor=([0-9]+)')::smallint, 100) AS fillfactor,
          current_setting('block_size')::numeric AS bs,
          CASE WHEN version()~'mingw32' OR version()~'64-bit|x86_64|ppc64|ia64|amd64' THEN 8 ELSE 4 END AS ma,
          24 AS page_hdr,
          23 + CASE WHEN MAX(coalesce(s.null_frac,0)) > 0 THEN ( 7 + count(s.attname) ) / 8 ELSE 0::int END
           + CASE WHEN bool_or(att.attname = 'oid' and att.attnum < 0) THEN 4 ELSE 0 END AS tpl_hdr_size,
          sum( (1-coalesce(s.null_frac, 0)) * coalesce(s.avg_width, 0) ) AS tpl_data_size
        FROM pg_attribute AS att
          JOIN pg_class AS tbl ON att.attrelid = tbl.oid
          JOIN pg_namespace AS ns ON ns.oid = tbl.relnamespace
          LEFT JOIN pg_stats AS s ON s.schemaname=ns.nspname
            AND s.tablename = tbl.relname AND s.inherited=false AND s.attname=att.attname
          LEFT JOIN pg_class AS toast ON tbl.reltoastrelid = toast.oid
        WHERE NOT att.attisdropped
          AND tbl.relkind = 'r'
        GROUP BY 1,2,3,4,5,6,7,8,9,10
        ORDER BY 2,3
      ) AS s
    ) AS s2
  ) AS s3
) AS s4;
    """  # noqa


class probe_btree_bloat(SqlProbe):
    # Btree index bloat estimation probe
    timeout = 30
    level = 'database'
    sql = """
SELECT
  current_database() AS dbname,
  SUM(bloat_size) / SUM(indexes_size) * 100 AS ratio
FROM (
  SELECT
    SUM(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(indexname)))::BIGINT AS indexes_size
  FROM pg_catalog.pg_indexes
  GROUP BY schemaname
) AS indexes,
(
  SELECT
    SUM(bloat_size) AS bloat_size,
    schemaname
  FROM (
    %s
  ) AS a
  GROUP BY schemaname
) AS ibloat
WHERE schemaname !~ '^pg_temp'
AND schemaname !~ '^pg_toast';
"""  % (INDEX_BTREE_BLOAT_SQL) # noqa
