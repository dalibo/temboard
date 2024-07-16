import logging
from os import path

import tornado.web

from temboardui.web.tornado import Blueprint, TemplateRenderer

logger = logging.getLogger(__name__)
blueprint = Blueprint()
blueprint.generic_proxy("/pgconf/configuration", methods=["POST", "GET"])
blueprint.generic_proxy("/pgconf/configuration/categories", methods=["GET"])
blueprint.generic_proxy("/pgconf/configuration/status", methods=["GET"])
blueprint.generic_proxy("/pgconf/configuration/category/.*", methods=["GET"])
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + "/templates")


class PGConfPlugin:
    def __init__(self, app):
        self.app = app

    def load(self):
        self.app.tornado_app.add_rules(blueprint.rules)
        self.app.tornado_app.add_rules(
            [
                (
                    r"/js/pgconf/(.*)",
                    tornado.web.StaticFileHandler,
                    {"path": plugin_path + "/static/js"},
                ),
                (
                    r"/css/pgconf/(.*)",
                    tornado.web.StaticFileHandler,
                    {"path": plugin_path + "/static/css"},
                ),
            ]
        )


@blueprint.instance_route("/pgconf/configuration", methods=["GET"])
def configuration_handler(request):
    request.instance.check_active_plugin("pgconf")
    request.instance.fetch_status()

    return render_template(
        "configuration.html",
        nav=True,
        role=request.current_user,
        instance=request.instance,
        plugin="pgconf",
    )
