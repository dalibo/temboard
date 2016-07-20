import os
import sys
import imp
import time
from temboardagent.logger import get_logger
from temboardagent.spc import connector, error
from temboardagent.errors import HTTPError

def load_plugins_configurations(config):
    """
    Intend to load plugins and run their configuration() function.
    Plugins are defined as a module located in plugins/ directory. The list
    of plugins to load is set into temboard section of the configuration file:
        [temboard]
        plugins = [ "plugin1", "plugin2" ]
    """

    # Get this module's path.
    path = os.path.dirname(__file__)
    ret = dict()
    # Get the logger.
    logger = get_logger(config)
    # PostgreSQL version
    pg_version = 0

    while pg_version == 0:
        try:
            conn = connector(
                host = config.postgresql['host'],
                port = config.postgresql['port'],
                user = config.postgresql['user'],
                password = config.postgresql['password'],
                database = config.postgresql['dbname']
            )
            """ Trying to get PostgreSQL version number. """
            conn.connect()
            pg_version = conn.get_pg_version()
            conn.close()
        except Exception as e:
            logger.error("Not able to get PostgreSQL version number.")
            try:
                conn.close()
            except Exception:
                pass

        # If we reach this point, PostgreSQL is not available, so we
        # wait 5 seconds and try again
        if pg_version == 0:
            time.sleep(5)

    # Loop through each plugin listed in the configuration file.
    for plugin_name in config.temboard['plugins']:
        logger.info("Loading plugin '%s'." % (plugin_name,))
        try:
            # Loading compat.py file
            fp_s, pathname_s, description_s = imp.find_module('compat', [path + '/plugins/'+plugin_name])
            module_compat = imp.load_module('compat', fp_s, pathname_s, description_s)
            # Check modules's PG_MIN_VERSION
            try:
                if (module_compat.PG_MIN_VERSION > pg_version):
                    # Version not supported
                    logger.error("-> PostgreSQL version (%s) is not supported by this plugin (min:%s)."
                                    % (pg_version, module_compat.PG_MIN_VERSION))
                    continue
                else:
                    logger.info("-> PostgreSQL version (%s) is supported by this plugin." % (pg_version))
            except ValueError as e:
                # PG_MIN_VERSION not set
                pass
        except Exception as e:
            pass
        try:
            # Locate and load the module with imp.
            fp, pathname, description = imp.find_module(plugin_name, [path + '/plugins'])
            module = imp.load_module(plugin_name, fp, pathname, description)
            # Try to run module's configuration() function.
            logger.info("-> loading configuration.")
            plugin_configuration = getattr(module, 'configuration')(config)
            ret.update({module.__name__: plugin_configuration})
            fp.close()
        except AttributeError as e:
            if fp:
                fp.close()
            logger.error("-> error: %s" % str(e))
        except Exception as e:
            if fp:
                fp.close()
            logger.error("-> error: %s" % str(e))

    return ret

# Global var to keep a track of timestamp of the last plugin's scheduler() function call.
PLUGINS_LAST_SCHEDULE = {}

def exec_scheduler(queue_in, config, commands, logger):
    """
    In charge of running the scheduling function of each plugin.
    """
    global PLUGINS_LAST_SCHEDULE
    for plugin_name in config.plugins:
        first_run = False
        if not (plugin_name in sys.modules):
            # The plugin seems not to be loaded.
            continue
        if not ('scheduler_interval' in config.plugins[plugin_name]):
            # If scheduler_interval is not set, we don't want to run it.
            continue
        if not (plugin_name in PLUGINS_LAST_SCHEDULE):
            # Check if this is the first shoot.
            PLUGINS_LAST_SCHEDULE[plugin_name] = time.time()
            first_run = True
        if not first_run  and (time.time() - PLUGINS_LAST_SCHEDULE[plugin_name]) < \
             config.plugins[plugin_name]['scheduler_interval']:
            continue
        try:
            # Call plugin's scheduler() function.
            getattr(sys.modules[plugin_name], 'scheduler')(queue_in, config, commands)
            PLUGINS_LAST_SCHEDULE[plugin_name] = time.time()
        except AttributeError as e:
            # scheduler() function does not exist.
            pass
        except Exception as e:
            logger.error("scheduler - %s: %s" % (plugin_name, str(e)))
