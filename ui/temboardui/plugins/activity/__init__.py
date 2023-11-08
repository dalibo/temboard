from os import path

from ...web.tornado import (
    Blueprint,
    TemplateRenderer,
)


blueprint = Blueprint()
blueprint.generic_proxy(r'/activity/kill', methods=['POST'])
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + '/templates')


class ActivityPlugin(object):
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        self.app.tornado_app.add_rules(blueprint.rules)

    def unload(self):
        raise NotImplementedError()


@blueprint.instance_route(r'/activity')
def activity(request):
    request.instance.check_active_plugin('activity')
    agent_username = request.instance.get_username()
    xsession = request.instance.xsession if agent_username else None
    request.instance.fetch_status()
    return render_template(
        'activity.html',
        nav=True,
        agent_username=agent_username,
        instance=request.instance,
        plugin='activity',
        xsession=xsession,
        role=request.current_user,
    )


@blueprint.instance_proxy(r'/activity')
def activity_proxy(request):
    request.instance.check_active_plugin('activity')
    return dict(
        blocking=request.instance.get('/activity/blocking'),
        running=request.instance.get('/activity'),
        waiting=request.instance.get('/activity/waiting'),
    )
