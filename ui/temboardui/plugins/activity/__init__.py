from os import path

from ...web.tornado import Blueprint, TemplateRenderer


blueprint = Blueprint()
blueprint.generic_proxy(r"/activity/kill", methods=["POST"])
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + "/templates")


class ActivityPlugin:
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        self.app.tornado_app.add_rules(blueprint.rules)


@blueprint.instance_route(r"/activity")
def activity(request):
    request.instance.check_active_plugin("activity")
    request.instance.fetch_status()
    return render_template(
        "activity.html",
        nav=True,
        instance=request.instance,
        plugin="activity",
        role=request.current_user,
    )


@blueprint.instance_proxy(r"/activity")
def activity_proxy(request):
    request.instance.check_active_plugin("activity")
    return dict(
        blocking=request.instance.get("/activity/blocking"),
        running=request.instance.get("/activity"),
        waiting=request.instance.get("/activity/waiting"),
    )
