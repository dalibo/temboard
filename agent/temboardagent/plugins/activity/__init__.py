import logging

from bottle import Bottle, default_app, request

from . import functions as activity_functions
from ...notification import NotificationMgmt, Notification
from ...tools import validate_parameters
from ...queries import QUERIES


bottle = Bottle()
logger = logging.getLogger(__name__)


@bottle.get('/')
def get_activity(pgconn):
    limit = int(request.query.get('limit', 300))
    return activity_functions.get_activity(pgconn, limit)


@bottle.get('/waiting')
def get_activity_waiting(pgconn):
    return activity_functions.get_activity_waiting(pgconn)


@bottle.get('/blocking')
def get_activity_blocking(pgconn):
    return activity_functions.get_activity_blocking(pgconn)


@bottle.post('/kill')
def post_activity_kill(pgconn):
    app = default_app().temboard
    validate_parameters(request.json, [
        ('pids', int, True)
    ])
    backends = []
    for pid in request.json['pids']:
        killed = pgconn.queryscalar(
            "SELECT pg_terminate_backend(%s) AS killed" % (pid))
        backends.append(dict(pid=pid, killed=killed))

        # Push a notification.
        try:
            NotificationMgmt.push(
                app.config,
                Notification(
                    username=request.username,
                    message="Backend %s terminated" % (pid)
                )
            )
        except Exception:
            logger.exception("Failed to push notification:")

    return dict(backends=backends)


LOCKS_COLUMNS = [
    'pid',
    'locktype',
    'database',
    'schema',
    'relation',
    'mode',
    'granted',
    'blocking_pid',
    'waitstart',
    'waiting_pids',
]


@bottle.get('/locks')
def get_locks(pgconn):
    # Returns waiting and blocking locks

    discover = default_app().temboard.discover.ensure_latest()
    if discover['postgres']['version_num'] < 100000:
        try:
            LOCKS_COLUMNS.remove('waitstart')
        except ValueError:
            pass

    limit = int(request.query.get('limit', 300))
    query = QUERIES['activity-locks'] + " LIMIT %d" % limit

    return dict(
        columns=SESSION_COLUMNS,
        rows=[row for row in pgconn.query(query)],
    )


SESSION_COLUMNS = [
    'pid',
    'client_addr',
    'username',
    'application_name',
    'database',
    'state',
    'backend_start',
    'query_start',
    'query',
    'waiting',
    'blocking',
]


@bottle.get('/sessions')
def get_sessions(pgconn):
    # List client session with blocking informations.

    limit = int(request.query.get('limit', 300))
    query = QUERIES['activity-sessions'] + " LIMIT %d" % limit
    rows = []
    for row in pgconn.query(query):
        try:
            data = read_proc_info(row['pid'])
            row['cpu_time'] = sum((
                data['utime'],
                data['stime'],
                data['cutime'],
                data['cstime'],
            ))
            row['memory'] = data['VmRSS']
            row['proc_state'] = data['state']
            row['proc_read'] = data['read_bytes']
            row['proc_write'] = data['write_bytes']
        except OSError as e:
            logger.debug("Failed to read /proc/%s info: %s.", row['pid'], e)
            row.update(dict(
                cpu_time=None,
                memory=None,
                proc_read=None,
                proc_state=None,
                proc_write=None,
            ))

        rows.append(row)

    return dict(
        columns=SESSION_COLUMNS,
        rows=rows,
    )


def read_proc_info(pid):
    procdir = '/proc/%d' % pid
    data = dict()
    with open(procdir + '/status') as fo:
        data.update(parse_proc_human(fo, 'VmRSS'))

    with open(procdir + '/stat') as fo:
        data.update(parse_proc_stat(fo.read()))
    with open(procdir + '/io') as fo:
        data.update(parse_proc_human(
            fo,
            'read_bytes', 'write_bytes',
        ))
    return data


def parse_proc_stat(raw):
    values = raw.split()
    return dict(
        state=values[2],
        utime=int(values[13]),
        stime=int(values[14]),
        cutime=int(values[15]),
        cstime=int(values[16]),
    )


def parse_proc_human(fo, *keys):
    # Parse human readable proc format
    data = dict()
    for line in fo:
        key, value = line.split(':')
        if keys and key not in keys:
            continue
        value = value.strip()
        if value.endswith(' kB'):
            value = int(value[:-3]) * 1024
        try:
            value = int(value)
        except ValueError:
            pass
        data[key] = value
    return data


class ActivityPlugin:
    PG_MIN_VERSION = (90400, 9.4)

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        default_app().mount('/activity', bottle)
