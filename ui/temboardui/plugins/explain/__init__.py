from typing import NamedTuple

from flask import current_app, g, request
from flask import render_template as flask_render_template

from ...web.flask import instance_proxy, instance_routes

PLUGIN_NAME = "explain"


class ExplainPlugin:
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        instance_proxy.generic_proxy("/explain", method="POST")


class ExplainOption(NamedTuple):
    name: str
    default: bool
    description: str


def list_options(pg_version):
    options = [
        ExplainOption(
            "VERBOSE", False, "Display additional information regarding the plan."
        ),
        ExplainOption(
            "COSTS",
            True,
            "Include information on the estimated startup and total cost of each plan node, as well as the estimated number of rows and the estimated width of each row.",
        ),
    ]
    buffers_description = "Include information on buffer usage."
    if pg_version > 180000:
        buffers_option = ExplainOption("BUFFERS", True, buffers_description)
    else:
        buffers_option = ExplainOption("BUFFERS", False, buffers_description)
    options.append(buffers_option)
    if pg_version > 100000:
        options.append(
            ExplainOption(
                "SUMMARY",
                False,
                "Include summary information (e.g., totaled timing information) after the query plan.",
            )
        )
    if pg_version > 120000:
        options.append(
            ExplainOption(
                "SETTINGS", False, "Include information on configuration parameters."
            )
        )
    if pg_version > 160000:
        options.append(
            ExplainOption(
                "GENERIC_PLAN",
                False,
                "Allow the statement to contain parameter placeholders like $1, and generate a generic plan that does not depend on the values of those parameters.",
            )
        )
    if pg_version > 170000:
        options.append(
            ExplainOption(
                "MEMORY",
                False,
                "Include information on memory consumption by the query planning phase.",
            )
        )
    return options


@instance_routes.route("/explain", methods=["GET", "POST"])
def post_explain():
    current_app.instance.check_active_plugin("explain")
    current_app.instance.fetch_status()
    if request.method == "POST":
        body = request.form.to_dict()
        query = body["query"]
    else:
        query = ""
    discover = g.instance.discover
    version_num = discover["postgres"]["version_num"]
    options = [option._asdict() for option in list_options(version_num)]

    return flask_render_template(
        "explain/index.html", plugin=PLUGIN_NAME, query=query, options=options
    )
