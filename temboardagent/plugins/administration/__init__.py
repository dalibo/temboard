import logging
import time

from temboardagent.routing import RouteSet
from temboardagent.tools import validate_parameters
from temboardagent.spc import error
from temboardagent.command import (
    oneline_cmd_to_array,
    exec_script,
)
from temboardagent.toolkit.configuration import OptionSpec
from temboardagent.toolkit.validators import quoted
from temboardagent.notification import NotificationMgmt, Notification

from . import functions as admin_functions
from .types import T_CONTROL


logger = logging.getLogger(__name__)
routes = RouteSet()


@routes.get(b'/administration/pg_version')
def api_pg_version(http_context, app):
    with app.postgres.connect() as conn:
        return admin_functions.pg_version(conn)


@routes.post(b'/administration/control')
def post_pg_control(http_context, app):
    # Control instance
    validate_parameters(http_context['post'], [
        ('action', T_CONTROL, False)
    ])
    action = http_context['post']['action']
    logger.info("PostgreSQL '%s' requested." % action)
    NotificationMgmt.push(app.config,
                          Notification(username=http_context['username'],
                                       message="PostgreSQL %s" % action))

    cmd = app.config.administration.pg_ctl % action
    cmd_args = oneline_cmd_to_array(cmd)
    (rcode, stdout, stderr) = exec_script(cmd_args)
    if rcode != 0:
        raise Exception(str(stderr))
    # Let's check if PostgreSQL is up & running after having executed
    # 'start' or 'restart' action.
    if action in ['start', 'restart']:
        # When a start/restart operation is requested, after the
        # startup/pg_ctl script has been executed then we check that
        # postgres is up & running:
        # while the PG conn. is not working then, for 10 seconds (max)
        # we'll check (connect/SELECT 1/disconnect) the connection, every
        # 0.5 second.
        retry = True
        t_start = time.time()
        while retry:
            try:
                with app.postgres.connect() as conn:
                    conn.execute('SELECT 1')
                    logger.info("Done.")
                    return dict(action=action, state='ok')
            except error:
                if (time.time() - t_start) > 10:
                    logger.info("Failed.")
                    return dict(action=action, state='ko')
            logger.info("Retrying...")
            time.sleep(0.5)

    elif action == 'stop':
        # Check the PG conn is not working anymore.
        try:
            retry = True
            t_start = time.time()
            while retry:
                with app.postgres.connect() as conn:
                    conn.execute('SELECT 1')
                time.sleep(0.5)
                if (time.time() - t_start) > 10:
                    retry = False
            logger.info("Failed.")
            return dict(action=action, state='ko')
        except error:
            logger.info("Done.")
            return dict(action=action, state='ok')

    elif action == 'reload':
        logger.info("Done.")
        return dict(action=action, state='ok')


class AdministrationPlugin(object):
    PG_MIN_VERSION = (90400, 9.4)
    options_specs = [
        OptionSpec('administration', 'pg_ctl', default=None, validator=quoted),
    ]

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.options_specs)

    def load(self):
        self.app.router.add(routes)

    def unload(self):
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.options_specs)
