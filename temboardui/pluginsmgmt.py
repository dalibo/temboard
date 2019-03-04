import imp
import logging
import os

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
        fp, pathname, description = imp.find_module(plugin_name,
                                                    [path + '/plugins'])
        try:
            module = imp.load_module(plugin_name, fp, pathname, description)
        except Exception:
            logger.exception("Failed to load %s module.", plugin_name)
            continue
        finally:
            if fp:
                fp.close()

        # Try to run module's configuration() function.
        try:
            ret.update({module.__name__: {
                'configuration': getattr(module, 'configuration')(config),
                'routes': getattr(module, 'get_routes')(config),
                'workers': getattr(module, 'workers', None),
            }})
        except Exception:
            logger.exception("Failed to load %s configuration.", plugin_name)
            continue
        logger.info("Loaded plugin '%s'." % (plugin_name, ))

    return ret
