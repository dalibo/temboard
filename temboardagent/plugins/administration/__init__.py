import time
import pickle
import base64
import os
try:
    from configparser import NoOptionError
except ImportError:
    from  ConfigParser import NoOptionError

from temboardagent.routing import add_route, add_worker
from temboardagent.api_wrapper import *
from temboardagent.logger import set_logger_name, get_logger
from temboardagent.configuration import (PluginConfiguration, ConfigurationError,
                                    Configuration)
from temboardagent.tools import validate_parameters
from temboardagent.types import *
from temboardagent.sharedmemory import Command
from temboardagent.tools import hash_id
from temboardagent.errors import (HTTPError, SharedItem_exists,
                SharedItem_no_free_slot_left, SharedItem_not_found, NotificationError)
from temboardagent.workers import COMMAND_START, COMMAND_DONE, COMMAND_ERROR
from temboardagent.spc import connector, error
from temboardagent.command import exec_command, oneline_cmd_to_array, exec_script
from temboardagent.notification import NotificationMgmt, Notification

import administration.functions as admin_functions
from administration.types import *

@add_route('GET', '/administration/pg_version')
def api_pg_version(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("administration")
    return api_function_wrapper_pg(config, http_context, sessions, admin_functions, 'pg_version')

@add_route('POST', '/administration/control')
def post_pg_control(http_context, queue_in = None, config = None, sessions = None, commands = None):
    # NOTE: in this case we don't want to use api functions wrapper, it leads
    # to "Broken pipe" error with debian init.d on start/restart. This is
    # probably due to getattr() call.
    set_logger_name("administration")
    # Get a new logger.
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)
    post = http_context['post']
    # Check POST parameters.
    validate_parameters(post, [
        ('action', T_CONTROL, False)
    ])

    try:
        session = sessions.get_by_sessionid(http_context['headers']['X-Session'].encode('utf-8'))
        NotificationMgmt.push(config, Notification(
                                        username = session.username,
                                        message = "PostgreSQL %s" % (post['action'])))
    except NotificationError as e:
        logger.error(e.message)

    cmd_args = oneline_cmd_to_array(config.plugins['administration']['pg_ctl'] % (post['action']))
    (rcode, stdout, stderr) = exec_script(cmd_args)
    if rcode != 0:
        raise HTTPError(408, str(stderr))
    # Let's check if postgresql is up & running on 'start' or 'restart' action.
    if post['action'] in ['start', 'restart']:
        conn = connector(
            host = config.postgresql['host'],
            port = config.postgresql['port'],
            user = config.postgresql['user'],
            password = config.postgresql['password'],
            database = config.postgresql['dbname']
        )
        # When a start/restart operation is requested, after the startup/pg_ctl
        # script is executed we check that postgres is up & running: while the
        # PG connection is not working, during 10 seconds (max) we'll check
        # (connect/SELECT 1/disconnect) the connection, every 0.5 second.
        retry = True
        t_start = time.time()
        while retry:
            try:
                conn.connect()
                conn.execute('SELECT 1')
                conn.close()
                return {'action': post['action'], 'state': 'ok'}
            except error as e:
                if (time.time() - t_start) > 10:
                    try:
                        conn.close()
                    except error as e:
                        pass
                    except Exception:
                        pass
                    return {'action': post['action'], 'state': 'ko'}
            time.sleep(0.5)

    elif post['action'] == 'stop':
        conn = connector(
            host = config.postgresql['host'],
            port = config.postgresql['port'],
            user = config.postgresql['user'],
            password = config.postgresql['password'],
            database = config.postgresql['dbname']
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
            return {'action': post['action'], 'state': 'ko'}
        except error as e:
            return {'action': post['action'], 'state': 'ok'}
    return {'action': post['action'], 'state': 'ok'}

@add_route('POST', '/administration/vacuum')
def api_vacuum(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("administration")
    worker = b'vacuum'
    # Get a new logger.
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)
    post = http_context['post']
    # Check POST parameters.
    validate_parameters(post, [
        ('database', T_OBJECTNAME, False),
        ('table', T_OBJECTNAME, False),
        ('mode', T_VACUUMMODE, False)
    ])
    # Serialize parameters.
    parameters = base64.b64encode(
                    pickle.dumps({
                        'database': post['database'],
                        'table': post['table'],
                        'mode': post['mode']
    })).decode('utf-8')
    # Check command uniqueness.
    try:
        commands.check_uniqueness(worker, parameters)
    except SharedItem_exists:
        raise HTTPError(402, "Command already issued.")
    cid =  hash_id(worker + b'-' + parameters.encode('utf-8'))
    command =  Command(
            cid.encode('utf-8'),
            time.time(),
            0,
            worker,
            parameters,
            0,
            u'')
    try:
        commands.add(command)
        # Put the Command in the command queue
        queue_in.put(command)
        return {"cid": cid}
    except SharedItem_no_free_slot_left as e:
        raise HTTPError(500, "Internal error.")

@add_worker(b'vacuum')
def worker_vacuum(commands, command, config):
    start_time = time.time() * 1000
    set_logger_name("administration_worker")
    logger = get_logger(config)
    logger.info("[vacuum] Starting: pid=%s commandid=%s" % (os.getpid(), command.commandid,))
    command.state = COMMAND_START
    command.time = time.time()
    commands.update(command)
    parameters = pickle.loads(base64.b64decode(command.parameters))
    logger.info("[vacuum] table=%s, mode=%s, database=%s"
                    % (parameters['table'], parameters['mode'], parameters['database'],))
    conn = connector(
        host = config.postgresql['host'],
        port = config.postgresql['port'],
        user = config.postgresql['user'],
        password = config.postgresql['password'],
        database = parameters['database']
    )
    try:
        conn.connect()
        if parameters['mode'] == 'standard':
            query = "VACUUM %s" % (parameters['table'],)
        else:
            query = "VACUUM %s %s" % (parameters['mode'], parameters['table'],)
        conn.execute(query)
        conn.close()
    except error as e:
        command.state = COMMAND_ERROR
        command.result = str(e.message)
        command.time = time.time()
        commands.update(command)
        logger.error("%s" % (str(e.message)))
        try:
            conn.close()
        except error as e:
            pass
        except Exception:
            pass
        return
    command.state = COMMAND_DONE
    command.time = time.time()
    commands.update(command)
    logger.info("[vacuum] done in %s s." % (str((time.time()*1000 - start_time)/1000),))

def configuration(config):
    class Configuration(PluginConfiguration):
        def __init__(self, config, *args, **kwargs):
            PluginConfiguration.__init__(self, config.configfile, *args, **kwargs)

            self.plugin_configuration = {
                'pg_ctl': None,
            }
            set_logger_name("administration")
            logger = get_logger(config)

            try:
                self.check_section(__name__)
            except ConfigurationError as e:
                return

            try:
                val =  self.get(__name__, 'pg_ctl')
                for char in ['"', '\'']:
                    if val.startswith(char) and val.endswith(char):
                        val = val[1:-1]
                self.plugin_configuration['pg_ctl'] = val
            except configparser.NoOptionError as e:
                pass

    c = Configuration(config)
    return c.plugin_configuration
