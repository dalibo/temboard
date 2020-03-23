from os import path
import tornado.web
import random

from temboardui.web import (
    Blueprint,
    TemplateRenderer,
    jsonify,
)
from temboardui.plugins.monitoring.tools import (
    get_request_ids,
    parse_start_end,
)


blueprint = Blueprint()
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + '/templates')


def configuration(config):
    return {}


def get_routes(config):
    routes = blueprint.rules + [
        (r"/js/statements/(.*)", tornado.web.StaticFileHandler, {
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


@blueprint.instance_route(r'/statements/data')
def data(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    # fake random data
    data = {
            "data": [
                {
                    "username": "postgres",
                    "dbname": random.choice(["bench", "tpc", "database"]),
                    "queryid": random.randint(0, 10000000),
                    "query": random.choice(["SELECT pg_sleep($1)",
                                            "SELECT count(*) FROM mytable",
                                            "SELECT count(*) FROM commandes cmd JOIN lignes_commandes lc ON lc.numero_commande = cmd.numero_commande WHERE cmd.client_id = $1"]), # noqa
                    "calls": random.choice(range(1000)),
                    "total_time": random.random() * 5000,
                    "min_time": 1001.583008,
                    "max_time": 1001.583008,
                    "mean_time": 1001.583008,
                    "stddev_time": 0,
                    "rows": 1,
                    "shared_blks_hit": 0,
                    "shared_blks_read": 0,
                    "shared_blks_dirtied": 0,
                    "shared_blks_written": 0,
                    "local_blks_hit": 0,
                    "local_blks_read": 0,
                    "local_blks_dirtied": 0,
                    "local_blks_written": 0,
                    "temp_blks_read ": 0,
                    "temp_blks_written": 0,
                    "blk_read_time": 0,
                    "blk_write_time": 0
                }
                for i in range(10)]
            }

    return jsonify(data=data)


@blueprint.instance_route(r'/statements')
def statements(request):
    request.instance.check_active_plugin(__name__)
    return render_template(
        'index.html',
        nav=True,
        agent_username=get_agent_username(request),
        instance=request.instance,
        plugin=__name__,
        role=request.current_user,
    )
