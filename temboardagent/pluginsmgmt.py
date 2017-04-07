import os
import sys
import imp
import time
from temboardagent.logger import get_logger, get_tb
from temboardagent.spc import connector


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
                host=config.postgresql['host'],
                port=config.postgresql['port'],
                user=config.postgresql['user'],
                password=config.postgresql['password'],
                database=config.postgresql['dbname']
            )
            """ Trying to get PostgreSQL version number. """
            conn.connect()
            pg_version = conn.get_pg_version()
            conn.close()
        except Exception as e:
            logger.traceback(get_tb())
            logger.error(str(e))
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
            fp_s, path_s, desc_s = imp.find_module(
                                        'compat',
                                        [path+'/plugins/'+plugin_name])
            module_compat = imp.load_module('compat',
                                            fp_s,
                                            path_s,
                                            desc_s)
            # Check modules's PG_MIN_VERSION
            try:
                if (module_compat.PG_MIN_VERSION > pg_version):
                    # Version not supported
                    logger.error("PostgreSQL version (%s) is not supported "
                                 "(min:%s)." % (pg_version,
                                                module_compat.PG_MIN_VERSION))
                    logger.info("Failed.")
                    continue
            except ValueError as e:
                # PG_MIN_VERSION not set
                pass
        except Exception as e:
            if fp_s:
                fp_s.close()
            logger.info("Not able to load the compatibility file: compat.py.")
        logger.info("Done.")
        try:
            # Locate and load the module with imp.
            fp, pathname, description = imp.find_module(plugin_name,
                                                        [path+'/plugins'])
            module = imp.load_module(plugin_name, fp, pathname, description)
            # Try to run module's configuration() function.
            logger.info("Loading plugin '%s' configuration." % (plugin_name))
            plugin_configuration = getattr(module, 'configuration')(config)
            ret.update({module.__name__: plugin_configuration})
            logger.info("Done.")
        except AttributeError as e:
            logger.info("No configuration.")
        except Exception as e:
            if fp:
                fp.close()
            logger.traceback(get_tb())
            logger.error(str(e))
            logger.info("Failed.")

    return ret


# Global var to keep a track of timestamp of the last plugin's scheduler()
# function call.
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
        if not first_run and (
                (time.time() - PLUGINS_LAST_SCHEDULE[plugin_name]) <
                config.plugins[plugin_name]['scheduler_interval']):
            continue
        try:
            logger.debug("Running %s.scheduler()" % (plugin_name))
            # Call plugin's scheduler() function.
            getattr(sys.modules[plugin_name], 'scheduler')(queue_in,
                                                           config,
                                                           commands)
            PLUGINS_LAST_SCHEDULE[plugin_name] = time.time()
            logger.debug("Done.")
        except AttributeError as e:
            # scheduler() function does not exist.
            logger.debug("Function does not exist.")
            pass
        except Exception as e:
            logger.traceback(get_tb())
            logger.error(str(e))
            logger.debug("Failed.")
