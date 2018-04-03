import time
import os
import sys
import re
import logging
import signal
import json
import urllib2
import collections

try:
    from configparser import NoOptionError
except ImportError:
    from ConfigParser import NoOptionError


from temboardagent.scheduler import taskmanager
from temboardagent.routing import add_route, add_worker
from temboardagent.configuration import (
    PluginConfiguration,
    ConfigurationError,
)
from temboardagent.errors import (
    HTTPError,
    SharedItem_exists,
    SharedItem_no_free_slot_left,
)
from temboardagent.api import check_sessionid
from temboardagent.queue import Queue, Message
from temboardagent.tools import now
from temboardagent.inventory import SysInfo

from monitoring.inventory import host_info, instance_info
from monitoring.probes import (
    load_probes,
    probe_bgwriter,
    probe_blocks,
    probe_cpu,
    probe_db_size,
    probe_filesystems_size,
    probe_loadavg,
    probe_locks,
    probe_memory,
    probe_process,
    probe_replication,
    probe_sessions,
    probe_tblspc_size,
    probe_wal_files,
    probe_xacts,
    run_probes,
)
from monitoring.output import send_output, remove_passwords

__VERSION__ = '0.0.1'

logger = logging.getLogger(__name__)


@add_route('GET', '/monitoring/probe/sessions')
def monitoring_probe_sessions(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_sessions(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/xacts')
def monitoring_probe_xacts(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_xacts(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/locks')
def monitoring_probe_locks(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_locks(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/blocks')
def monitoring_probe_blocks(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_blocks(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/bgwriter')
def monitoring_probe_bgwriter(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_bgwriter(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/db_size')
def monitoring_probe_db_size(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_db_size(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/tblspc_size')
def monitoring_probe_tblspc_size(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_tblspc_size(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/filesystems_size')
def monitoring_probe_filesystems_size(http_context, config=None,
                                      sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(
            probe_filesystems_size(config.plugins['monitoring']),
            config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/cpu')
def monitoring_probe_cpu(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_cpu(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/process')
def monitoring_probe_process(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_process(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/memory')
def monitoring_probe_memory(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_memory(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/loadavg')
def monitoring_probe_loadavg(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_loadavg(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/wal_files')
def monitoring_probe_wal_files(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_wal_files(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/replication')
def monitoring_probe_replication(http_context, config=None, sessions=None):
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_replication(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


def api_run_probe(probe_instance, config):
    """
    Run a probe instance.
    """
    config.plugins['monitoring']['conninfo'] = [{
        'host': config.postgresql['host'],
        'port': config.postgresql['port'],
        'user': config.postgresql['user'],
        'database': config.postgresql['dbname'],
        'password': config.postgresql['password'],
        'dbnames': config.plugins['monitoring']['dbnames'],
        'instance': config.postgresql['instance']
    }]
    # Validate connection information from the config, and ensure
    # the instance is available
    instances = []
    sysinfo = SysInfo()
    hostname = sysinfo.hostname(config.temboard['hostname'])
    for conninfo in config.plugins['monitoring']['conninfo']:
        logging.debug("Validate connection information on instance \"%s\"",
                      conninfo['instance'])
        instances.append(instance_info(conninfo, hostname))

    # Set home path
    probe_instance.set_home(config.temboard['home'])
    # Gather the data from probes
    data = run_probes([probe_instance], instances, delta=False)
    return data


@taskmanager.worker(pool_size=1)
def monitoring_collector_worker(config):
    """
    Run probes and push collected metrics in a queue.
    """
    signal.signal(signal.SIGTERM, monitoring_worker_sigterm_handler)
    # convert config dict to namedtuple
    config = collections.namedtuple('__config', ['temboard', 'plugins',
                                                 'postgresql', 'logging'])(
                    temboard=config['temboard'],
                    plugins=config['plugins'],
                    postgresql=config['postgresql'],
                    logging=config['logging']
                )

    logger.debug("Starting collector")

    try:
        system_info = host_info(config.temboard['hostname'])
    except (ValueError, Exception) as e:
        logger.exception(e)
        logger.debug("Failed")
        sys.exit(1)

    # Load the probes to run
    try:
        probes = load_probes(config.plugins['monitoring'],
                             config.temboard['home'])
        config.plugins['monitoring']['conninfo'] = [{
            'host': config.postgresql['host'],
            'port': config.postgresql['port'],
            'user': config.postgresql['user'],
            'database': config.postgresql['dbname'],
            'password': config.postgresql['password'],
            'dbnames': config.plugins['monitoring']['dbnames'],
            'instance': config.postgresql['instance']
        }]

        # Validate connection information from the config, and ensure
        # the instance is available
        instances = []
        for conninfo in config.plugins['monitoring']['conninfo']:
            instances.append(instance_info(conninfo, system_info['hostname']))

        logger.debug("Running probes")
        # Gather the data from probes
        data = run_probes(probes, instances)

        # Prepare and send output
        output = {
            'datetime': now(),
            'hostinfo': system_info,
            'instances': remove_passwords(instances),
            'data': data,
            'version': __VERSION__
        }
        logger.debug(output)
        q = Queue('%s/metrics.q' % (config.temboard['home']),
                  max_size=1024 * 1024 * 10, overflow_mode='slide')
        q.push(Message(content=json.dumps(output)))
        logger.debug("Done")
    except Exception as e:
        logger.exception(e)
        logger.error("Could not collect data")
        sys.exit(1)


@taskmanager.worker(pool_size=1)
def monitoring_sender_worker(config):
    signal.signal(signal.SIGTERM, monitoring_worker_sigterm_handler)
    # convert config dict to namedtuple
    config = collections.namedtuple('__config', ['temboard', 'plugins',
                                                 'postgresql', 'logging'])(
                    temboard=config['temboard'],
                    plugins=config['plugins'],
                    postgresql=config['postgresql'],
                    logging=config['logging']
                )

    c = 0
    logger.debug("Starting sender")
    while True:
        # Let's do it smoothly..
        time.sleep(0.5)

        q = Queue('%s/metrics.q' % (config.temboard['home']),
                  max_size=1024 * 1024 * 10, overflow_mode='slide')
        msg = q.shift(delete=False)
        if msg is None:
            break
        try:
            send_output(config.plugins['monitoring']['ssl_ca_cert_file'],
                        config.plugins['monitoring']['collector_url'],
                        config.temboard['key'],
                        msg.content)
        except urllib2.HTTPError as e:
            logger.exception(e)
            # On an error 409 (DB Integrity) we need to remove the message.
            if int(e.code) != 409:
                logger.error("Failed with code=%s message=%s"
                             % (e.code, e.msg))
                sys.exit(1)
        except Exception as e:
            logger.exception(e)
            logger.error("Failed")
            sys.exit(1)

        # If everything's fine then remove current msg from the queue
        q.shift(delete=True, check_msg=msg)

        if c > 60:
            break
        c += 1
    logger.debug("Done")


@taskmanager.bootstrap()
def monitoring_bootstrap(context):
    conf = context.get('config')
    yield taskmanager.Task(
            worker_name='monitoring_collector_worker',
            id='monitoring_collector',
            options={'config': conf},
            redo_interval=conf['plugins']['monitoring']['scheduler_interval'],
    )
    yield taskmanager.Task(
            worker_name='monitoring_sender_worker',
            id='monitoring_sender',
            options={'config': conf},
            redo_interval=conf['plugins']['monitoring']['scheduler_interval'],
    )


def configuration(config):
    class Configuration(PluginConfiguration):
        def __init__(self, config, *args, **kwargs):
            PluginConfiguration.__init__(self, config.configfile, *args,
                                         **kwargs)

            self.plugin_configuration = {
                'dbnames': '*',
                'scheduler_interval': 60,
                'probes': '*',
                'collector_url': os.environ.get(
                    'TEMBOARD_MONITORING_COLLECTOR_URL', None),
                'ssl_ca_cert_file': None
            }

            try:
                self.check_section(__name__)
            except ConfigurationError:
                return

            try:
                dbnames = self.get(__name__, 'dbnames')
                self.plugin_configuration['dbnames'] = re.split(r'[,\s]+',
                                                                dbnames)
            except NoOptionError:
                pass

            try:
                probes = self.get(__name__, 'probes')
                self.plugin_configuration['probes'] = re.split(r'[,\s]+',
                                                               probes)
            except NoOptionError:
                pass

            try:
                collector_url = self.get(__name__, 'collector_url')
                self.plugin_configuration['collector_url'] = collector_url
            except NoOptionError:
                pass

            try:
                if not (self.getint(__name__, 'scheduler_interval') > 0 and
                        self.getint(__name__, 'scheduler_interval') < 86400):
                    raise ValueError()
                self.plugin_configuration['scheduler_interval'] = \
                    self.getint(__name__, 'scheduler_interval')
            except ValueError:
                logger.error("%s - configuration error: 'scheduler_interval' "
                             "must be an integer between 0 and 86400 in '%s' "
                             "section in %s."
                             % (__name__, self.configfile, __name__))
            except NoOptionError:
                pass

            try:
                self.plugin_configuration['ssl_ca_cert_file'] = (
                    self.getfile(__name__, 'ssl_ca_cert_file'))
            except NoOptionError:
                pass

    c = Configuration(config)
    return c.plugin_configuration


def monitoring_worker_sigterm_handler(signum, frame):
    logging.info("monitoring_worker - SIGTERM")
    sys.exit(1)
