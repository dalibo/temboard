import imp
import logging
import os
import sys

logger = logging.getLogger(__name__)


def load_plugins(plugin_names, config):
    """
    Intend to load plugins and run their configuration() function.
    Plugins are defined as a module located in plugins/ directory. Plugins list
    to load is declared into temboard section of the configuration file:
        [temboard]
        plugins = [ "plugin1", "plugin2" ]
    """

    # Get this module's path.
    path = os.path.dirname(os.path.realpath(__file__))
    ret = dict()
    # Loop through declared plugins.
    for plugin_name in plugin_names:
        # Locate and load the module with imp.
        logger.info("Loading plugin '%s'." % (plugin_name, ))
        fp, pathname, description = imp.find_module(plugin_name,
                                                    [path + '/plugins'])
        try:
            module = imp.load_module(plugin_name, fp, pathname, description)
            # Try to run module's configuration() function.
            logger.info("Loading plugin '%s' configuration." % (plugin_name, ))
            ret.update({
                module.__name__: {
                    'configuration': getattr(module, 'configuration')(config),
                    'routes': getattr(module, 'get_routes')(config)
                }
            })
            fp.close()
        except AttributeError as e:
            if fp:
                fp.close()
        except Exception as e:
            logger.exception(str(e))
    return ret


def plugins_bind_metadata(engine, plugin_names):
    for plugin_name in plugin_names:
        if plugin_name in sys.modules:
            try:
                getattr(sys.modules[plugin_name], 'bind_metadata')(engine)
            except AttributeError:
                pass
