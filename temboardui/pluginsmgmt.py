import logging
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

    ret = dict()
    # Loop through declared plugins.
    for plugin_name in plugin_names:
        try:
            __import__('temboardui.plugins', fromlist=[plugin_name])
            module = sys.modules['temboardui.plugins.' + plugin_name]
        except Exception:
            logger.exception("Failed to load %s module.", plugin_name)
            continue

        # Try to run module's configuration() function.
        try:
            ret.update({plugin_name: {
                'configuration': getattr(module, 'configuration')(config),
                'routes': getattr(module, 'get_routes')(config),
                'workers': getattr(module, 'workers', None),
            }})
        except Exception:
            logger.exception("Failed to load %s configuration.", plugin_name)
            continue
        logger.info("Loaded plugin '%s'." % (plugin_name, ))

    return ret
