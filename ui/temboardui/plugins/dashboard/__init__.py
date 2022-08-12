import logging
from os.path import realpath

import tornado.web
from tornado.escape import json_encode

from ...agentclient import TemboardAgentClient
from ...web.tornado import (
    Blueprint,
    TemplateRenderer,
)


blueprint = Blueprint()
blueprint.generic_proxy(r"/dashboard")
logger = logging.getLogger(__name__)
plugin_path = realpath(__file__ + '/..')
render_template = TemplateRenderer(plugin_path + '/templates')


class DashboardPlugin(object):
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        self.app.tornado_app.add_rules(blueprint.rules)
        self.app.tornado_app.add_rules([
            (r"/js/dashboard/(.*)", tornado.web.StaticFileHandler, {
                'path': plugin_path + "/static/js"
            }),
        ])


@blueprint.instance_route(r"/dashboard")
def dashboard(request):
    request.instance.check_active_plugin('dashboard')

    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        agent_username = None

    try:
        config = request.instance.get('/dashboard/config')
    except TemboardAgentClient.Error as e:
        if 404 != e.code:
            raise
        logger.debug("Fallback dashboard config.")
        config = {
            'history_length': 150,
            'scheduler_interval': 2
        }

    history = request.instance.get('/dashboard/history')
    if history:
        last_data = history[-1]
    else:
        last_data = request.instance.get('/dashboard/live')

    return render_template(
        'dashboard.html',
        nav=True, role=request.current_user,
        instance=request.instance,
        agent_username=agent_username,
        plugin='dashboard',
        config=json_encode(config),
        dashboard=last_data,
        history=json_encode(history or ''),
    )
