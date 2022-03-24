from builtins import object
import logging

from temboardui.web import Blueprint, anonymous_allowed
from temboardui.toolkit.configuration import OptionSpec


blueprint = Blueprint()
logger = logging.getLogger(__name__)


@blueprint.route("/sample/", json=True)
@anonymous_allowed
def get_sample(request):
    logger.debug("GET /sample/")
    return {
        "message": "Sample response.",
        "sample": True,
        "option": request.config.sample.option,
    }


class SamplePlugin(object):
    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs([OptionSpec('sample', 'option')])
        logger.info("Plugin sample initialized.")

    def load(self):
        logger.info("Plugin sample loaded.")
        self.app.webapp.add_rules(blueprint.rules)
