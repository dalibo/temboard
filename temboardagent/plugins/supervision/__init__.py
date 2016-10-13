import time
import os
import sys
import re
import logging
import signal
import json
import urllib2

try:
    from configparser import NoOptionError
except ImportError:
    from  ConfigParser import NoOptionError


from temboardagent.routing import add_route, add_worker
from temboardagent.configuration import (PluginConfiguration, ConfigurationError,
                                    Configuration)
from temboardagent.logger import get_logger, set_logger_name, get_tb
from temboardagent.sharedmemory import Command
from temboardagent.tools import hash_id
from temboardagent.errors import (HTTPError, SharedItem_exists,
                SharedItem_no_free_slot_left, SharedItem_not_found)
from temboardagent.workers import COMMAND_START, COMMAND_DONE, COMMAND_ERROR
from temboardagent.command import exec_command
from temboardagent.pluginsmgmt import load_plugins_configurations
from temboardagent.api import check_sessionid
from temboardagent.queue import Queue, Message
from temboardagent.tools import now, check_fqdn
from temboardagent.inventory import SysInfo

from supervision.inventory import host_info, instance_info
from supervision.probes import *
from supervision.output import send_output, remove_passwords

__VERSION__ = '0.0.1'

@add_route('GET', '/supervision/probe/sessions')
def supervision_probe_sessions(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_sessions(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/xacts')
def supervision_probe_xacts(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_xacts(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/locks')
def supervision_probe_locks(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_locks(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/blocks')
def supervision_probe_blocks(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_blocks(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/bgwriter')
def supervision_probe_bgwriter(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_bgwriter(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/db_size')
def supervision_probe_db_size(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_db_size(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/tblspc_size')
def supervision_probe_tblspc_size(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_tblspc_size(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/filesystems_size')
def supervision_probe_filesystems_size(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_filesystems_size(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/cpu')
def supervision_probe_cpu(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_cpu(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/process')
def supervision_probe_process(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_process(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/memory')
def supervision_probe_memory(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_memory(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/loadavg')
def supervision_probe_loadavg(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_loadavg(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/wal_files')
def supervision_probe_wal_files(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_wal_files(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

@add_route('GET', '/supervision/probe/replication')
def supervision_probe_replication(http_context, queue_in = None, config = None, sessions = None, commands = None):
    set_logger_name("supervision")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_replication(config.plugins['supervision']), config)
        return output
    except (Exception, error) as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")

def api_run_probe(probe_instance, config):
    """
    Run a probe instance.
    """
    set_logger_name("supervision")
    logger = get_logger(config)
    # TODO: logging methods in supervision_agent code and supervision_agent should be aligned.
    logging.root = logger
    config.plugins['supervision']['conninfo'] = [{
        'host': config.postgresql['host'],
        'port': config.postgresql['port'],
        'user': config.postgresql['user'],
        'database': config.postgresql['dbname'],
        'password': config.postgresql['password'],
        'dbnames': config.plugins['supervision']['dbnames'],
        'instance': config.postgresql['instance']
    }]
    # Validate connection information from the config, and ensure
    # the instance is available
    instances = []
    sysinfo = SysInfo()
    hostname = sysinfo.hostname(config.temboard['hostname'])
    for conninfo in config.plugins['supervision']['conninfo']:
        logging.debug("Validate connection information on instance \"%s\"", conninfo['instance'])
        instances.append(instance_info(conninfo, hostname))

    # Gather the data from probes
    data = run_probes([probe_instance], instances, delta = False)
    return data


@add_worker(b'supervision_collector')
def supervision_collector_worker(commands, command, config):
    """
    Run probes and push collected metrics in a queue.
    """
    signal.signal(signal.SIGTERM, supervision_worker_sigterm_handler)

    start_time = time.time() * 1000
    set_logger_name("supervision_collector_worker")
    logger = get_logger(config)
    # TODO: logging methods in supervision plugin must be aligned.
    logging.root = logger
    logger.debug("Starting with pid=%s" % (os.getpid()))
    logger.debug("commandid=%s" % (command.commandid))
    command.state = COMMAND_START
    command.time = time.time()

    try:
        command.pid = os.getpid()
        commands.update(command)
        system_info = host_info(config.temboard['hostname'])
    except (ValueError, Exception) as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        sys.exit(1)

   # Load the probes to run
    try:
        probes = load_probes(config.plugins['supervision'], config.temboard['home'])
        config.plugins['supervision']['conninfo'] = [{
            'host': config.postgresql['host'],
            'port': config.postgresql['port'],
            'user': config.postgresql['user'],
            'database': config.postgresql['dbname'],
            'password': config.postgresql['password'],
            'dbnames': config.plugins['supervision']['dbnames'],
            'instance': config.postgresql['instance']
        }]

        # Validate connection information from the config, and ensure
        # the instance is available
        instances = []
        for conninfo in config.plugins['supervision']['conninfo']:
            logging.debug("Validate connection information on instance \"%s\"", conninfo['instance'])
            instances.append(instance_info(conninfo, system_info['hostname']))

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
        logger.debug("Collected data: %s" % (output))
        q = Queue('%s/metrics.q'% (config.temboard['home']), max_size = 1024 * 1024 * 10, overflow_mode = 'slide')
        q.push(Message(content = json.dumps(output)))
    except Exception as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        sys.exit(1)

    logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
    logger.debug("Done.")

@add_worker(b'supervision_sender')
def supervision_sender_worker(commands, command, config):
    signal.signal(signal.SIGTERM, supervision_worker_sigterm_handler)
    start_time = time.time() * 1000
    set_logger_name("supervision_sender_worker")
    logger = get_logger(config)
    # TODO: logging methods in supervision plugin must be aligned.
    logging.root = logger
    logger.debug("Starting with pid=%s" % (os.getpid()))
    logger.debug("commandid=%s" % (command.commandid))
    command.state = COMMAND_START
    command.time = time.time()
    command.pid = os.getpid()
    commands.update(command)
    c = 0
    while True:
        # Let's do it smoothly..
        time.sleep(0.5)

        q = Queue('%s/metrics.q' % (config.temboard['home']), max_size = 1024 * 1024 * 10, overflow_mode = 'slide')
        msg = q.shift(delete = False)
        if msg is None:
            break
        try:
            send_output(config.plugins['supervision']['ssl_ca_cert_file'],
                    config.plugins['supervision']['collector_url'],
                    config.plugins['supervision']['agent_key'],
                    msg.content)
        except urllib2.HTTPError as e:
            logger.traceback(get_tb())
            logger.error(str(e))
            # On an error 409 (DB Integrity) we need to remove the message.
            if int(e.code) != 409:
                logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
                logger.debug("Failed.")
                sys.exit(1)
        except Exception as e:
            logger.traceback(get_tb())
            logger.error(str(e))
            logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
            logger.debug("Failed.")
            sys.exit(1)
        _ = q.shift(delete = True, check_msg = msg)
        if c > 60:
            break
        c += 1
    logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
    logger.debug("Done.")

def scheduler(queue_in, config, commands):
    # Schedule collector worker.
    schedule_worker(queue_in, config, commands, b'supervision_collector')
    # Schedule sender worker.
    schedule_worker(queue_in, config, commands, b'supervision_sender')

def schedule_worker(queue_in, config, commands, worker, parameters = ''):
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
                'dbnames': '*',
                'scheduler_interval': 60,
                'probes': '*',
                'agent_key': None,
                'collector_url': None,
                'ssl_ca_cert_file': None
            }
            set_logger_name("supervision")
            logger = get_logger(config)

            try:
                self.check_section(__name__)
            except ConfigurationError as e:
                return

            try:
                dbnames = self.get(__name__, 'dbnames')
                self.plugin_configuration['dbnames'] = re.split(r'[,\s]+', dbnames)
            except NoOptionError as e:
                pass

            try:
                probes = self.get(__name__, 'probes')
                self.plugin_configuration['probes'] = re.split(r'[,\s]+', probes)
            except NoOptionError as e:
                pass

            try:
                agent_key = self.get(__name__, 'agent_key')
                self.plugin_configuration['agent_key'] = agent_key
            except NoOptionError as e:
                pass

            try:
                collector_url = self.get(__name__, 'collector_url')
                self.plugin_configuration['collector_url'] = collector_url
            except NoOptionError as e:
                pass

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
                with open(self.get(__name__, 'ssl_ca_cert_file')) as fd:
                    _ = fd.read()
                    self.plugin_configuration['ssl_ca_cert_file'] = self.get(__name__, 'ssl_ca_cert_file')
            except Exception as e:
                raise ConfigurationError("SSL CA certificates file %s can't be opened."
                        % (self.get(__name__, 'ssl_ca_cert_file')))
            except configparser.NoOptionError as e:
                pass

    c = Configuration(config)
    return c.plugin_configuration

def supervision_worker_sigterm_handler(signum, frame):
    logging.info("supervision_worker - SIGTERM")
    sys.exit(1)
