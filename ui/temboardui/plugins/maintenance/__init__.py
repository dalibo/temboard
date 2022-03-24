from os import path
import tornado.web

from temboardui.web import (
    Blueprint,
    TemplateRenderer,
)


PLUGIN_NAME = 'maintenance'
blueprint = Blueprint()
blueprint.generic_proxy(r'/maintenance/.*/schema/.*/table/.*/'
                        '(?:vacuum|analyze)',
                        methods=['POST'])
blueprint.generic_proxy(r'/maintenance/.*/(?:vacuum|analyze)',
                        methods=['POST'])
blueprint.generic_proxy(r'/maintenance/.*/schema/.*/(?:index|table)/.*/'
                        '(?:reindex)',
                        methods=['POST'])
blueprint.generic_proxy(r'/maintenance/.*/(?:reindex)',
                        methods=['POST'])
blueprint.generic_proxy(r'/maintenance/reindex/.*',
                        methods=['DELETE'])
blueprint.generic_proxy(r'/maintenance/(?:vacuum|analyze)/.*',
                        methods=['DELETE'])
blueprint.generic_proxy(r'/maintenance/.*')
blueprint.generic_proxy(r'/maintenance')
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + '/templates')


def configuration(config):
    return {}


def get_routes(config):
    routes = blueprint.rules + [
        (r"/js/maintenance/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


def get_agent_username(request):
    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        agent_username = None
    return agent_username


@blueprint.instance_route(r'/maintenance')
def maintenance(request):
    request.instance.check_active_plugin(PLUGIN_NAME)
    return render_template(
        'index.html',
        nav=True,
        agent_username=get_agent_username(request),
        instance=request.instance,
        plugin=PLUGIN_NAME,
        role=request.current_user,
    )


@blueprint.instance_route(r'/maintenance/(.*)/schema/(.*)/table/(.*)')
def table(request, database, schema, table):
    request.instance.check_active_plugin(PLUGIN_NAME)
    agent_username = get_agent_username(request)
    xsession = request.instance.xsession if agent_username else None
    return render_template(
        'table.html',
        nav=True,
        agent_username=agent_username,
        instance=request.instance,
        plugin=PLUGIN_NAME,
        xsession=xsession,
        role=request.current_user,
        database=database,
        schema=schema,
        table=table,
    )


@blueprint.instance_route(r'/maintenance/(.*)/schema/(.*)')
def schema(request, database, schema):
    request.instance.check_active_plugin(PLUGIN_NAME)
    agent_username = get_agent_username(request)
    xsession = request.instance.xsession if agent_username else None
    return render_template(
        'schema.html',
        nav=True,
        agent_username=agent_username,
        instance=request.instance,
        plugin=PLUGIN_NAME,
        xsession=xsession,
        role=request.current_user,
        database=database,
        schema=schema,
    )


@blueprint.instance_route(r'/maintenance/(.*)')
def database(request, database):
    request.instance.check_active_plugin(PLUGIN_NAME)
    agent_username = get_agent_username(request)
    xsession = request.instance.xsession if agent_username else None
    return render_template(
        'database.html',
        nav=True,
        agent_username=get_agent_username(request),
        instance=request.instance,
        plugin=PLUGIN_NAME,
        xsession=xsession,
        role=request.current_user,
        database=database,
    )
