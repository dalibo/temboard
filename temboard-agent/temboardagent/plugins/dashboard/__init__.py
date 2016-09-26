import time
import signal
import json
from os import getpid
try:
    from configparser import NoOptionError
except ImportError:
    from  ConfigParser import NoOptionError

from temboardagent.routing import add_route
from temboardagent.api_wrapper import *
from temboardagent.logger import set_logger_name, get_tb
from temboardagent.spc import connector, error
from temboardagent.routing import add_route, add_worker
from temboardagent.configuration import (PluginConfiguration, ConfigurationError,
                                    Configuration)
from temboardagent.logger import get_logger, set_logger_name, get_tb
from temboardagent.sharedmemory import Command
from temboardagent.tools import hash_id
from temboardagent.errors import (HTTPError, SharedItem_exists,
                SharedItem_no_free_slot_left, SharedItem_not_found)
from temboardagent.workers import COMMAND_START, COMMAND_DONE, COMMAND_ERROR
from temboardagent.pluginsmgmt import load_plugins_configurations
from temboardagent.queue import Queue, Message
import dashboard.metrics

@add_route('GET', '/dashboard')
def dashboard(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard Fetch all
    @apiVersion 0.0.1
    @apiName GetDasboard
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object} active_backends
    @apiSuccess {Number} active_backends.nb Number of PostgreSQL active backends.
    @apiSuccess {Number} active_backends.time Timestamp (floating with ms) when the number of backend has been calculated.
    @apiSuccess {Number} loadaverage System loadaverage.
    @apiSuccess {String} os_version Operating system version.
    @apiSuccess {String} os_version PostgreSQL version.
    @apiSuccess {Number} hitratio PostgreSQL cache/hit ratio (%)
    @apiSuccess {Number} n_cpu Number of CPU.
    @apiSuccess {Object} databases
    @apiSuccess {String} databases.total_size PostgreSQL instance total size (with unit).
    @apiSuccess {String} databases.time Time when DBs informations have been retreived (HH:MM).
    @apiSuccess {Number} databases.databases Number of databases.
    @apiSuccess {Number} databases.total_commit Number of commited xact.
    @apiSuccess {Number} databases.total_rollback Number of rollbacked xact.
    @apiSuccess {Number} databases.timestamp Timestamp (floating with ms).
    @apiSuccess {Object} memory
    @apiSuccess {Number} memory.total Total amount of memory (kB).
    @apiSuccess {Number} memory.active Active memory (%).
    @apiSuccess {Number} memory.cached Memory used as OS cache (%).
    @apiSuccess {Number} memory.free Unused memory (%).
    @apiSuccess {String} hostname Machine hostname.
    @apiSuccess {Object} cpu
    @apiSuccess {Number} cpu.iowait CPU cycles waiting for I/O operation (%).
    @apiSuccess {Number} cpu.idle CPU IDLE time (%).
    @apiSuccess {Number} cpu.steal CPU steal time (%).
    @apiSuccess {Number} cpu.user CPU user time (%).
    @apiSuccess {Number} cpu.system CPU system time (%).
    @apiSuccess {Object} buffers
    @apiSuccess {Number} buffers.nb Allocated buffers from PostgreSQL bgwriter.
    @apiSuccess {Number} buffers.time Timestamp (floating with ms) when the buffers number has been fetched.

    @apiExample {curl} Example usage:
        curl -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" http://localhost:12345/dashboard

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "active_backends":
            {
                "nb": 1,
                "time": 1429617751.29224
            },
            "loadaverage": 0.28,
            "os_version": "Linux 3.16.0-34-generic x86_64",
            "pg_version": "9.4.1",
            "n_cpu": "4",
            "hitratio": 98.0,
            "databases":
            {
                "total_size": "1242 MB",
                "time": "14:02",
                "databases": 4,
                "total_commit": 16728291,
                "total_rollback": 873
            },
            "memory": {
                "total": 3950660,
                "active": 46.9,
                "cached": 20.2,
                "free": 32.9
            },
            "hostname": "neptune",
            "cpu":
            {
                "iowait": 0.0,
                "idle": 97.5,
                "steal": 0.0,
                "user": 2.5,
                "system": 0.0
            },
            "buffers":
            {
                "nb": 348247,
                "time": 1429617751.276508
            }
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_metrics_queue')

@add_route('GET', '/dashboard/live')
def dashboard_live(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_metrics')

@add_route('GET', '/dashboard/history')
def dashboard_history(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_history_metrics_queue')

@add_route('GET', '/dashboard/buffers')
def dashboard_buffers(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/buffers PostgreSQL bgwriter buffers
    @apiVersion 0.0.1
    @apiName GetDasboardBuffers
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object} buffers
    @apiSuccess {Number} buffers.nb Allocated buffers from PostgreSQL bgwriter.
    @apiSuccess {Number} buffers.time Timestamp (floating with ms) when the buffers number has been fetched.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/buffers

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:22:50 GMT
        Content-type: application/json

        {"buffers": {"nb": 348247, "time": 1429701770.303621}}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_buffers')

@add_route('GET', '/dashboard/hitratio')
def dashboard_hitratio(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/hitratio PostgreSQL cache hit ratio
    @apiVersion 0.0.1
    @apiName GetDasboardHitratio
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Number} hitratio PostgreSQL global cache/hit ratio (%)

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/hitratio

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:27:27 GMT
        Content-type: application/json

        {"hitratio": 98.0}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_hitratio')

@add_route('GET', '/dashboard/active_backends')
def dashboard_active_backends(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/active_backends PostgreSQL active backends
    @apiVersion 0.0.1
    @apiName GetDasboardActiveBackends
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object} active_backends
    @apiSuccess {Number} active_backends.nb Number of PostgreSQL active backends.
    @apiSuccess {Number} active_backends.time Timestamp (floating with ms) when the number of backend has been calculated.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/active_backends

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:38:02 GMT
        Content-type: application/json

        {"active_backends": {"nb": 1, "time": 1429702682.228157}}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_active_backends')

@add_route('GET', '/dashboard/cpu')
def dashboard_cpu(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/cpu CPU usage
    @apiVersion 0.0.1
    @apiName GetDasboardCPU
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object} cpu
    @apiSuccess {Number} cpu.iowait CPU cycles waiting for I/O operation (%).
    @apiSuccess {Number} cpu.idle CPU IDLE time (%).
    @apiSuccess {Number} cpu.steal CPU steal time (%).
    @apiSuccess {Number} cpu.user CPU user time (%).
    @apiSuccess {Number} cpu.system CPU system time (%).

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/cpu

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:39:58 GMT
        Content-type: application/json

        {"cpu": {"iowait": 0.0, "idle": 97.5, "steal": 0.0, "user": 2.5, "system": 0.0}}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_cpu_usage')

@add_route('GET', '/dashboard/loadaverage')
def dashboard_loadaverage(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/loadaverage System loadaverage
    @apiVersion 0.0.1
    @apiName GetDasboardLoadaverage
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Number} loadaverage System loadaverage.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/loadaverage

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:41:31 GMT
        Content-type: application/json

        {"loadaverage": 0.31}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_loadaverage')

@add_route('GET', '/dashboard/memory')
def dashboard_memory(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/memory Memory usage
    @apiVersion 0.0.1
    @apiName GetDasboardMemory
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object} memory
    @apiSuccess {Number} memory.total Total amount of memory (kB).
    @apiSuccess {Number} memory.active Active memory (%).
    @apiSuccess {Number} memory.cached Memory used as OS cache (%).
    @apiSuccess {Number} memory.free Unused memory (%).

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/memory

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:44:14 GMT
        Content-type: application/json

        {"memory": {"total": 3950660,"active": 56.6, "cached": 33.8, "free": 9.6}}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_memory_usage')

@add_route('GET', '/dashboard/hostname')
def dashboard_hostname(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/hostname Machine hostname
    @apiVersion 0.0.1
    @apiName GetDasboardHostname
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {String} hostname Machine hostname.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/hostname

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:47:34 GMT
        Content-type: application/json

        {"hostname": "neptune"}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_hostname')

@add_route('GET', '/dashboard/os_version')
def dashboard_os_version(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/os_version Operating system version
    @apiVersion 0.0.1
    @apiName GetDasboardOSVersion
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {String} os_version Operating system version.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/os_version

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:49:19 GMT
        Content-type: application/json

        {"os_version": "Linux 3.16.0-34-generic x86_64"}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_os_version')

@add_route('GET', '/dashboard/pg_version')
def dashboard_pg_version(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/pg_version PostgreSQL version
    @apiVersion 0.0.1
    @apiName GetDasboardPGVersion
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {String} pg_version PostgreSQL version.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/pg_version

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:49:19 GMT
        Content-type: application/json

        {"pg_version": "9.4.1"}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_pg_version')

@add_route('GET', '/dashboard/n_cpu')
def dashboard_n_cpu(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/n_cpu Number of CPU
    @apiVersion 0.0.1
    @apiName GetDasboardNCpu
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Number} n_cpu Number of CPU.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/n_cpu

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:49:19 GMT
        Content-type: application/json

        {"n_cpu": 4}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper(config, http_context, sessions, metrics, 'get_n_cpu')

@add_route('GET', '/dashboard/databases')
def dashboard_databases(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /dashboard/databases PostgreSQL instance size & number of DB
    @apiVersion 0.0.1
    @apiName GetDasboardDatabases
    @apiGroup Dashboard

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object} databases
    @apiSuccess {String} databases.total_size PostgreSQL instance total size (with unit).
    @apiSuccess {String} databases.time Time when DBs informations have been retreived (HH:MM).
    @apiSuccess {Number} databases.databases Number of databases.
    @apiSuccess {Number} databases.total_commit Number of commited xact.
    @apiSuccess {Number} databases.total_rollback Number of rollbacked xact.

    @apiExample {curl} Example usage:
        curl -H "X-Session: <session-id>" http://localhost:12345/dashboard/databases

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 11:52:05 GMT
        Content-type: application/json

        {"databases": {"total_size": "1242 MB", "time": "13:52", "databases": 4, "total_commit": 16728291, "total_rollback": 873}}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}
    """
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_databases')

@add_route('GET', '/dashboard/info')
def dashboard_info(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("dashboard")
    return api_function_wrapper_pg(config, http_context, sessions, metrics, 'get_info')

def dashboard_worker_sigterm_handler(signum, frame):
    logging.info("Dashboard collector worker received SIGTERM")
    sys.exit(1)

@add_worker(b'dashboard_collector')
def dashboard_collector_worker(commands, command, config):
    try:
        signal.signal(signal.SIGTERM, dashboard_worker_sigterm_handler)
        start_time = time.time() * 1000
        set_logger_name("dashboard_collector")
        logger = get_logger(config)
        logger.debug("Starting with pid=%s" % (getpid()))
        logger.debug("commandid=%s" % (command.commandid))
        command.state = COMMAND_START
        command.time = time.time()
        command.pid = getpid()
        commands.update(command)

        conn = connector(
            host = config.postgresql['host'],
            port = config.postgresql['port'],
            user = config.postgresql['user'],
            password = config.postgresql['password'],
            database = config.postgresql['dbname']
        )
        conn.connect()
        db_metrics = metrics.get_metrics(conn, config)
        # We don't want to store notifications in the history.
        db_metrics.pop('notifications', None)

        conn.close()
        q = Queue('%s/dashboard.q'% (config.temboard['home']), max_length = (config.plugins['dashboard']['history_length']+1), overflow_mode = 'slide')
        q.push(Message(content = json.dumps(db_metrics)))
        logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
        logger.debug("Done.")
    except (error, Exception) as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        try:
            conn.close()
        except Exception:
            pass
        sys.exit(1)

def scheduler(queue_in, config, commands):
    logger = get_logger(config)
    worker = b'dashboard_collector'
    parameters = ''
    # Check command uniqueness.
    try:
        commands.check_uniqueness(worker, parameters)
    except SharedItem_exists:
        return

    cid =  hash_id(worker)
    command = Command(cid.encode('utf-8'), time.time(), 0, worker, parameters, 0, u'')
    try:
        commands.add(command)
        # Put the Command in the command queue
        queue_in.put(command)
        return
    except SharedItem_no_free_slot_left:
        return


def configuration(config):
    class Configuration(PluginConfiguration):
        def __init__(self, config, *args, **kwargs):
            PluginConfiguration.__init__(self, config.configfile, *args, **kwargs)

            self.plugin_configuration = {
                'scheduler_interval': 2,
                'history_length': 20
            }
            set_logger_name("dashboard")
            logger = get_logger(config)

            try:
                self.check_section(__name__)
            except ConfigurationError as e:
                return

            try:
                if not (self.getint(__name__, 'scheduler_interval') > 0 and \
                    self.getint(__name__, 'scheduler_interval') < 86400):
                    raise ValueError()
                self.plugin_configuration['scheduler_interval'] = \
                    self.getint(__name__, 'scheduler_interval')
            except ValueError as e:
                logger.error("%s - configuration error: 'scheduler_interval' must be"
                    "an integer between 0 and 86400 in '%s' section in %s."
                    % (__name__, self.configfile, __name__))
            except NoOptionError as e:
                pass

            try:
                if not (self.getint(__name__, 'history_length') > 0 and \
                    self.getint(__name__, 'history_length') < 300):
                    raise ValueError()
                self.plugin_configuration['history_length'] = \
                    self.getint(__name__, 'history_length')
            except ValueError as e:
                logger.error("%s - configuration error: 'histor_length' must be"
                    "an integer between 0 and 300 in '%s' section in %s."
                    % (__name__, self.configfile, __name__))
            except NoOptionError as e:
                pass

    c = Configuration(config)
    return c.plugin_configuration
