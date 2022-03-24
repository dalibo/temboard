from os import path
import tornado.web

from temboardui.web import (
    Blueprint,
    TemplateRenderer,
)


PLUGIN_NAME = 'activity'
blueprint = Blueprint()
blueprint.generic_proxy(r'/activity/kill', methods=['POST'])
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + '/templates')


def configuration(config):
    return {}


def get_routes(config):
    routes = blueprint.rules + [
        (r"/js/activity/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


def get_agent_username(request):
    try:
        return request.instance.get_profile()['username']
    except Exception:
        return None


@blueprint.instance_route(r'/activity/(running|blocking|waiting)')
def activity(request, mode):
    request.instance.check_active_plugin(PLUGIN_NAME)
    agent_username = get_agent_username(request)
    xsession = request.instance.xsession if agent_username else None
    return render_template(
        'activity.html',
        nav=True,
        agent_username=agent_username,
        instance=request.instance,
        plugin=PLUGIN_NAME,
        mode=mode,
        xsession=xsession,
        role=request.current_user,
    )


@blueprint.instance_proxy(r'/activity(?:/blocking|/waiting)?')
def activity_proxy(request):
    request.instance.check_active_plugin(PLUGIN_NAME)
    return dict(
        blocking=request.instance.get('/activity/blocking'),
        running=request.instance.get('/activity'),
        waiting=request.instance.get('/activity/waiting'),
    )
