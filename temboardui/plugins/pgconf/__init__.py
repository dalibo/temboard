import logging
from os import path
import tornado.web
from tornado.escape import url_escape, url_unescape

from temboardui.web import (
    Blueprint,
    HTTPError,
    Redirect,
    TemplateRenderer,
)


PLUGIN_NAME = 'pgconf'
logger = logging.getLogger(__name__)
blueprint = Blueprint()
blueprint.generic_proxy("/pgconf/configuration", methods=["POST"])
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + "/templates")


def configuration(config):
    return {}


def get_routes(config):
    routes = blueprint.rules + [
        (
            r"/js/pgconf/(.*)",
            tornado.web.StaticFileHandler,
            {'path': plugin_path + "/static/js"}
        ),
        (
            r"/css/pgconf/(.*)",
            tornado.web.StaticFileHandler,
            {'path': plugin_path + "/static/css"}
        ),
    ]
    return routes


@blueprint.instance_route("/pgconf/configuration(?:/category/(.+))?",
                          methods=["GET", "POST"])
def configuration_handler(request, category=None):
    request.instance.check_active_plugin(PLUGIN_NAME)
    profile = request.instance.get_profile()
    agent_username = profile['username']
    template_vars = {}
    # Deduplicate HTTP prefix of plugin on agent.
    prefix = "/pgconf/configuration"
    query_filter = request.handler.get_argument('filter', None, strip=True)

    status = request.instance.get(prefix + "/status")
    categories = request.instance.get(prefix + "/categories")

    if category:
        category = url_unescape(category)
    else:
        category = categories['categories'][0]
    logger.debug("category=%s", category)

    if query_filter:
        query = {'filter': query_filter}
        configuration_url = prefix
    else:
        query = {}
        configuration_url = prefix + "/category/" + url_escape(category)
    configuration = request.instance.get(configuration_url, query=query)

    if "POST" == request.method:
        settings = {'settings': [
            {'name': name, 'setting': value[0]}
            for name, value in request.arguments.iteritems()
            # 'filter' is not a setting, just ignore it.
            if name != 'filter'
        ]}
        try:
            request.instance.post(prefix, body=settings)
            # Redirect to GET page, same URI.
            return Redirect(request.uri)
        except HTTPError as e:
            # Rerender HTML page with errors.
            template_vars['error_code'] = e
            template_vars['error_message'] = e.log_message

    return render_template(
        'configuration.html',
        nav=True,
        role=request.current_user,
        instance=request.instance,
        agent_username=agent_username,
        plugin=PLUGIN_NAME,
        xsession=request.instance.xsession,
        current_cat=category,
        configuration_categories=categories,
        configuration_status=status,
        data=configuration,
        query_filter=query_filter,
        **template_vars
    )
