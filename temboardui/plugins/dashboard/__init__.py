import logging
from os.path import realpath

from tornado.escape import json_encode

from temboardui.temboardclient import TemboardError
from temboardui.web import (
    Blueprint,
    TemplateRenderer,
)


blueprint = Blueprint()
blueprint.generic_proxy(r"/dashboard")
logger = logging.getLogger(__name__)
plugin_path = realpath(__file__ + '/..')
render_template = TemplateRenderer(plugin_path + '/templates')


def configuration(config):
    return {}


def get_routes(config):
    return blueprint.rules


@blueprint.instance_route(r"/dashboard")
def dashboard(request):
    request.instance.check_active_plugin(__name__)

    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        agent_username = None

    try:
        config = request.instance.get('/dashboard/config')
    except TemboardError as e:
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
        plugin=__name__,
        config=json_encode(config),
        dashboard=last_data,
        history=json_encode(history or ''),
    )
