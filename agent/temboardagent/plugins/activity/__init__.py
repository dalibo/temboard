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


class ActivityPlugin:
    PG_MIN_VERSION = (90400, 9.4)

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        default_app().mount('/activity', bottle)
