from os import path
import tornado.web

from temboardui.web import (
    Blueprint,
    TemplateRenderer,
)
from temboardui.handlers.base import JsonHandler
from temboardui.async import (
    JSONAsyncResult,
    run_background,
)
from temboardui.errors import TemboardUIError
from temboardui.temboardclient import temboard_activity_kill


blueprint = Blueprint()
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + '/templates')


def configuration(config):
    return {}


def get_routes(config):
    handler_conf = {
        'ssl_ca_cert_file': config.temboard['ssl_ca_cert_file'],
        'template_path': plugin_path + "/templates"
    }
    routes = blueprint.rules + [
        (r"/proxy/(.*)/([0-9]{1,5})/activity/kill", ActivityKillProxyHandler,
         handler_conf),
        (r"/js/activity/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


@blueprint.instance_route(r'/activity/(running|blocking|waiting)')
def activity(request, mode):
    request.instance.check_active_plugin(__name__)
    profile = request.instance.get_profile()
    return render_template(
        'activity.html',
        nav=True,
        agent_username=profile['username'],
        instance=request.instance,
        plugin=__name__,
        mode=mode,
        xsession=request.instance.xsession,
        role=request.current_user,
    )


@blueprint.instance_proxy(r'/activity(?:/blocking|/waiting)?')
def activity_proxy(request):
    request.instance.check_active_plugin(__name__)
    return dict(
        blocking=request.instance.proxy('GET', '/activity/blocking').body,
        running=request.instance.proxy('GET', '/activity').body,
        waiting=request.instance.proxy('GET', '/activity/waiting').body,
    )


class ActivityKillProxyHandler(JsonHandler):

    @JsonHandler.catch_errors
    def post_kill(self, agent_address, agent_port):
        self.logger.info("Posting terminate backend.")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise TemboardUIError(401, 'X-Session header missing')

        self.logger.debug(tornado.escape.json_decode(self.request.body))
        data_kill = temboard_activity_kill(
            self.ssl_ca_cert_file, agent_address, agent_port, xsession,
            tornado.escape.json_decode(self.request.body))
        self.logger.info("Done.")
        return JSONAsyncResult(http_code=200, data=data_kill)

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_kill, self.async_callback, (agent_address,
                                                             agent_port))
