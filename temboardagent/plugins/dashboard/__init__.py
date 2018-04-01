import logging
import time
import signal
import json
import sys
import collections

from os import getpid
try:
    from configparser import NoOptionError
except ImportError:
    from ConfigParser import NoOptionError

from temboardagent.scheduler import taskmanager
from temboardagent.api_wrapper import (
    api_function_wrapper,
    api_function_wrapper_pg,
)
from temboardagent.spc import connector, error
from temboardagent.routing import add_route, add_worker
from temboardagent.configuration import (
    PluginConfiguration,
    ConfigurationError,
)
from temboardagent.errors import (
    SharedItem_exists,
    SharedItem_no_free_slot_left,
)
from temboardagent.queue import Queue, Message
import dashboard.config as config_module
import dashboard.metrics as metrics


logger = logging.getLogger(__name__)


@add_route('GET', '/dashboard')
def dashboard(http_context, config=None, sessions=None, commands=None):
    return api_function_wrapper(config, http_context, sessions, metrics,
                                'get_metrics_queue')


@add_route('GET', '/dashboard/config')
def dashboard_config(http_context, config=None, sessions=None):
    return api_function_wrapper(config, http_context, sessions, config_module,
                                'get_config')


@add_route('GET', '/dashboard/live')
def dashboard_live(http_context,
                   config=None,
                   sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_metrics')


@add_route('GET', '/dashboard/history')
def dashboard_history(http_context,
                      config=None,
                      sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_history_metrics_queue')


@add_route('GET', '/dashboard/buffers')
def dashboard_buffers(http_context,
                      config=None,
                      sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_buffers')


@add_route('GET', '/dashboard/hitratio')
def dashboard_hitratio(http_context,
                       config=None,
                       sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_hitratio')


@add_route('GET', '/dashboard/active_backends')
def dashboard_active_backends(http_context,
                              config=None,
                              sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_active_backends')


@add_route('GET', '/dashboard/cpu')
def dashboard_cpu(http_context,
                  config=None,
                  sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_cpu_usage')


@add_route('GET', '/dashboard/loadaverage')
def dashboard_loadaverage(http_context,
                          config=None,
                          sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_loadaverage')


@add_route('GET', '/dashboard/memory')
def dashboard_memory(http_context,
                     config=None,
                     sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_memory_usage')


@add_route('GET', '/dashboard/hostname')
def dashboard_hostname(http_context,
                       config=None,
                       sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_hostname')


@add_route('GET', '/dashboard/os_version')
def dashboard_os_version(http_context,
                         config=None,
                         sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_os_version')


@add_route('GET', '/dashboard/pg_version')
def dashboard_pg_version(http_context,
                         config=None,
                         sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_pg_version')


@add_route('GET', '/dashboard/n_cpu')
def dashboard_n_cpu(http_context,
                    config=None,
                    sessions=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                metrics,
                                'get_n_cpu')


@add_route('GET', '/dashboard/databases')
def dashboard_databases(http_context,
                        config=None,
                        sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_databases')


@add_route('GET', '/dashboard/info')
def dashboard_info(http_context,
                   config=None,
                   sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_info')


@add_route('GET', '/dashboard/max_connections')
def dashboard_max_connections(http_context,
                              config=None,
                              sessions=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   metrics,
                                   'get_max_connections')


def dashboard_worker_sigterm_handler(signum, frame):
    sys.exit(1)


@taskmanager.worker(pool_size=1)
def dashboard_collector_worker(config):
    try:
        signal.signal(signal.SIGTERM, dashboard_worker_sigterm_handler)
        logger.debug("Collecting data")
        conn = connector(
            host=config['postgresql']['host'],
            port=config['postgresql']['port'],
            user=config['postgresql']['user'],
            password=config['postgresql']['password'],
            database=config['postgresql']['dbname']
        )
        conn.connect()
        # convert config dict to namedtuple
        config_nt = collections.namedtuple(
                        '__config',
                        ['temboard', 'plugins', 'postgresql', 'logging']
                    )(
                        temboard=config['temboard'],
                        plugins=config['plugins'],
                        postgresql=config['postgresql'],
                        logging=config['logging']
                     )
        # Collect data
        data = metrics.get_metrics(conn, config_nt)
        conn.close()

        # We don't want to store notifications in the history.
        data.pop('notifications', None)
        q = Queue('%s/dashboard.q' % (config['temboard']['home']),
                  max_length=(config['plugins']['dashboard']['history_length']
                              +1),
                  overflow_mode='slide'
                  )
        q.push(Message(content=json.dumps(data)))
        logger.debug(data)
        logger.debug("End")
    except (error, Exception) as e:
        logger.error("Could not collect data")
        logger.exception(e)
        try:
            conn.close()
        except Exception:
            pass
        sys.exit(1)


@taskmanager.bootstrap()
def dashboard_collector_bootstrap(context):
    config = context.get('config')
    yield taskmanager.Task(
            worker_name='dashboard_collector_worker',
            id='dashboard_collector',
            options={'config': config},
            redo_interval=config['plugins']['dashboard']['scheduler_interval'],
    )


def configuration(config):
    class Configuration(PluginConfiguration):
        def __init__(self, config, *args, **kwargs):
            PluginConfiguration.__init__(self,
                                         config.configfile,
                                         *args,
                                         **kwargs)

            self.plugin_configuration = {
                'scheduler_interval': 2,
                'history_length': 150
            }

            try:
                self.check_section(__name__)
            except ConfigurationError:
                return

            try:
                if not (self.getint(__name__, 'scheduler_interval') > 0 and
                        self.getint(__name__, 'scheduler_interval') < 86400):
                    raise ValueError()
                self.plugin_configuration['scheduler_interval'] = \
                    self.getint(__name__, 'scheduler_interval')
            except ValueError:
                logger.error("%s - configuration error: 'scheduler_interval' "
                             "must be an integer between 0 and 86400 in "
                             "section '%s' in %s." % (
                                 __name__,
                                 self.configfile,
                                 __name__
                                 )
                             )
            except NoOptionError:
                pass

            try:
                if not (self.getint(__name__, 'history_length') > 0 and
                        self.getint(__name__, 'history_length') < 300):
                    raise ValueError()
                self.plugin_configuration['history_length'] = \
                    self.getint(__name__, 'history_length')
            except ValueError:
                logger.error("%s - configuration error: 'history_length' must "
                             "be an integer between 0 and 300 in section '%s'"
                             " in %s." % (
                                 __name__,
                                 self.configfile,
                                 __name__
                                 )
                             )
            except NoOptionError:
                pass

    c = Configuration(config)
    return c.plugin_configuration
