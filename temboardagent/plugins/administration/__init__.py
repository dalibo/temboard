import logging
import time
import pickle
import base64
import os
try:
    from configparser import NoOptionError
except ImportError:
    from ConfigParser import NoOptionError

from temboardagent.routing import add_route, add_worker
from temboardagent.api_wrapper import api_function_wrapper_pg
from temboardagent.configuration import (
    PluginConfiguration,
    ConfigurationError,
)
from temboardagent.api import check_sessionid
from temboardagent.tools import validate_parameters, hash_id
from temboardagent.types import T_OBJECTNAME
from temboardagent.errors import (
    HTTPError,
    SharedItem_exists,
    SharedItem_no_free_slot_left,
    SharedItem_not_found,
    NotificationError,
)
from temboardagent.spc import connector, error
from temboardagent.command import (
    oneline_cmd_to_array,
    exec_script,
)
from temboardagent.notification import NotificationMgmt, Notification

import administration.functions as admin_functions
from administration.types import T_CONTROL


logger = logging.getLogger(__name__)


@add_route('GET', '/administration/pg_version')
def api_pg_version(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   admin_functions,
                                   'pg_version')


@add_route('POST', '/administration/control')
def post_pg_control(http_context, config=None, sessions=None):
    # NOTE: in this case we don't want to use api functions wrapper, it leads
    # to "Broken pipe" error with debian init.d script on start/restart.
    # This is probably due to getattr() call.
    post = http_context['post']

    try:
        check_sessionid(http_context['headers'], sessions)
        # Check POST parameters.
        validate_parameters(post, [
            ('action', T_CONTROL, False)
        ])
        session = sessions.get_by_sessionid(
                    http_context['headers']['X-Session'].encode('utf-8')
                    )
    except (Exception, HTTPError) as e:
        logger.exception(str(e))
        logger.debug(http_context)
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")

    try:
        NotificationMgmt.push(config,
                              Notification(
                                username=session.username,
                                message="PostgreSQL %s" % post['action']
                                )
                              )
    except (NotificationError, Exception) as e:
        logger.exception(str(e))

    try:
        logger.info("PostgreSQL '%s' requested." % (post['action']))
        cmd_args = oneline_cmd_to_array(
                    config.plugins['administration']['pg_ctl'] % (
                        post['action']
                        )
                    )
        (rcode, stdout, stderr) = exec_script(cmd_args)
        if rcode != 0:
            raise Exception(str(stderr))
        # Let's check if PostgreSQL is up & running after having executed
        # 'start' or 'restart' action.
        if post['action'] in ['start', 'restart']:
            conn = connector(
                host=config.postgresql['host'],
                port=config.postgresql['port'],
                user=config.postgresql['user'],
                password=config.postgresql['password'],
                database=config.postgresql['dbname']
            )
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
                    conn.connect()
                    conn.execute('SELECT 1')
                    conn.close()
                    logger.info("Done.")
                    return {'action': post['action'], 'state': 'ok'}
                except error:
                    if (time.time() - t_start) > 10:
                        try:
                            conn.close()
                        except error:
                            pass
                        except Exception:
                            pass
                        logger.info("Failed.")
                        return {'action': post['action'], 'state': 'ko'}
                time.sleep(0.5)

        elif post['action'] == 'stop':
            conn = connector(
                host=config.postgresql['host'],
                port=config.postgresql['port'],
                user=config.postgresql['user'],
                password=config.postgresql['password'],
                database=config.postgresql['dbname']
            )
            # Check the PG conn is not working anymore.
            try:
                retry = True
                t_start = time.time()
                while retry:
                    conn.connect()
                    conn.execute('SELECT 1')
                    conn.close()
                    time.sleep(0.5)
                    if (time.time() - t_start) > 10:
                        retry = False
                logger.info("Failed.")
                return {'action': post['action'], 'state': 'ko'}
            except error:
                logger.info("Done.")
                return {'action': post['action'], 'state': 'ok'}
        logger.info("Done.")
        return {'action': post['action'], 'state': 'ok'}
    except (Exception, error, HTTPError) as e:
        logger.exception(str(e))
        logger.info("Failed")
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")


def configuration(config):
    class Configuration(PluginConfiguration):
        def __init__(self, config, *args, **kwargs):
            PluginConfiguration.__init__(self,
                                         config.configfile,
                                         *args,
                                         **kwargs)

            self.plugin_configuration = {
                'pg_ctl': None,
            }

            try:
                self.check_section(__name__)
            except ConfigurationError:
                return

            try:
                val = self.get(__name__, 'pg_ctl')
                for char in ['"', '\'']:
                    if val.startswith(char) and val.endswith(char):
                        val = val[1:-1]
                self.plugin_configuration['pg_ctl'] = val
            except NoOptionError:
                pass

    c = Configuration(config)
    return c.plugin_configuration
