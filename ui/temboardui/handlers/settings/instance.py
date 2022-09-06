import codecs
import logging

from temboardui.application import (
    add_instance,
    add_instance_in_group,
    add_instance_plugin,
    check_agent_address,
    check_agent_port,
    delete_instance,
    delete_instance_from_group,
    get_group_list,
    get_groups_by_instance,
    get_instance_list,
    purge_instance_plugins,
    update_instance,
)
from temboardui.agentclient import TemboardAgentClient
from temboardui.web.tornado import (
    HTTPError,
    InstanceHelper,
    admin_required,
    app,
    render_template,
    Response,
)
from ...toolkit.pycompat import StringIO
from ...model import QUERIES
from ...plugins.monitoring import collector as monitoring_collector
from ...plugins.statements import statements_pull1


logger = logging.getLogger(__name__)


def add_instance_in_groups(db_session, instance, groups):
    for group_name in groups or []:
        add_instance_in_group(
            db_session, instance.agent_address, instance.agent_port,
            group_name)


def create_instance_helper(db_session, data):
    validate_instance_data(data)
    groups = data.pop('groups')
    plugins = data.pop('plugins') or []
    instance = add_instance(db_session, **data)
    add_instance_in_groups(db_session, instance, groups)
    enable_instance_plugins(
        db_session, instance, plugins, app.config.temboard.plugins,
    )

    if 'monitoring' in plugins:
        logger.info("Schedule monitoring collect for agent now.")
        monitoring_collector.defer(
            address=data['new_agent_address'],
            port=data['new_agent_port'],
            key=data['agent_key'],
        )

    if 'statements' in plugins:
        logger.info("Schedule statements collect for agent now.")
        statements_pull1.defer(
            host=data['new_agent_address'],
            port=data['new_agent_port'],
        )


def enable_instance_plugins(db_session, instance, plugins, loaded_plugins):
    for plugin_name in plugins or []:
        # 'administration' plugin case: the plugin is not currently
        # implemented on UI side
        if plugin_name == 'administration':
            continue
        if plugin_name not in loaded_plugins:
            raise HTTPError(404, "Unknown plugin %s." % plugin_name)

        add_instance_plugin(
            db_session, instance.agent_address,
            instance.agent_port, plugin_name)


def validate_instance_data(data):
    # Submited attributes checking.
    if not data.get('new_agent_address'):
        raise HTTPError(400, "Agent address is missing.")
    check_agent_address(data['new_agent_address'])
    if 'new_agent_port' not in data or data['new_agent_port'] == '':
        raise HTTPError(400, "Agent port is missing.")
    check_agent_port(str(data['new_agent_port']))
    if 'groups' not in data:
        raise HTTPError(400, "Groups field is missing.")
    if data['groups'] is not None and type(data['groups']) != list:
        raise HTTPError(400, "Invalid group list.")


@app.route(r"/json/settings/instance", methods=['POST'])
@admin_required
def create_instance_handler(request):
    create_instance_helper(request.db_session, request.json)
    return {"message": "OK"}


@app.route(
    r"/json/settings/instance" + InstanceHelper.INSTANCE_PARAMS,
    methods=['GET', 'POST'], with_instance=True)
@admin_required
def json_instance(request):
    instance = request.instance
    if 'GET' == request.method:
        groups = get_group_list(request.db_session, 'instance')
        data = instance.asdict()
        data.update({
            'agent_key': instance.agent_key,
            'cpu': instance.cpu,
            'memory_size': instance.memory_size,
            'pg_version': instance.pg_version,
            'pg_version_summary': instance.pg_version_summary,
            'server_groups': [{
                'name': group.group_name,
                'description': group.group_description
            } for group in groups],
            'server_plugins': request.config.temboard.plugins,
        })
        return data
    else:  # POST (update)
        data = request.json
        validate_instance_data(data)
        groups = data.pop('groups')
        plugins = data.pop('plugins') or []

        # First step is to remove the instance from the groups it belongs to.
        instance_groups = get_groups_by_instance(
            request.db_session, instance.agent_address,
            instance.agent_port)
        for instance_group in instance_groups:
            delete_instance_from_group(
                request.db_session, instance.agent_address,
                instance.agent_port, instance_group.group_name)
        # Remove plugins
        purge_instance_plugins(
            request.db_session, instance.agent_address,
            instance.agent_port)

        instance = update_instance(
            request.db_session,
            instance.agent_address,
            instance.agent_port,
            **data)
        add_instance_in_groups(request.db_session, instance, groups)
        enable_instance_plugins(
            request.db_session, instance, plugins,
            request.config.temboard.plugins,
        )
        return {"message": "OK"}


@app.route(r"/json/settings/delete/instance$", methods=['POST'])
@admin_required
def json_delete_instance(request):
    data = request.json
    if not data.get('agent_address'):
        raise HTTPError(400, "Agent address field is missing.")
    if not data.get('agent_port'):
        raise HTTPError(400, "Agent port field is missing.")
    delete_instance(request.db_session, **data)
    return {'delete': True}


@app.route(
    r"/json/discover/instance" + InstanceHelper.INSTANCE_PARAMS)
@admin_required
def discover(request, address, port):
    client = TemboardAgentClient.factory(
        request.config,
        address, port,
        key=request.headers.get('X-TemBoard-Agent-Key'),
        username=request.current_user.role_name,
    )
    try:
        response = client.get('/discover')
        response.raise_for_status()
    except OSError as e:
        logger.error(
            "Failed to discover agent at %s:%s: %s",  address, port, e)
        raise HTTPError(400, (
            "Can't connect to agent. "
            "Please check address and port or that agent is running."))
    else:
        # pass-through JSON
        return response.json()


@app.route(r"/settings/instances")
@admin_required
def instances(request):
    return render_template(
        'settings/instance.html',
        nav=True, role=request.current_user,
        instance_list=get_instance_list(request.db_session)
    )


@app.route(r"/settings/instances.csv")
@admin_required
def instances_csv(request):
    search = request.handler.get_query_argument('filter')
    search = '%%%s%%' % search if search else '%'
    bind = request.db_session.get_bind()
    conn = bind.raw_connection().connection
    sql = QUERIES['copy-instances-as-csv']
    with conn.cursor() as cur, StringIO() as fo:
        sql = cur.mogrify(sql, (search,))
        cur.copy_expert(sql, fo)
        csv = fo.getvalue()

    filename = 'postgresql-instances-inventory.csv'
    return Response(
        status_code=200,
        headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment;filename=' + filename,
        },
        # BOM declares UTF8 for Excell.
        body=codecs.BOM_UTF8 + csv.encode('utf-8'),
    )


@app.route(r"/json/register/instance", methods=['POST'])
@admin_required
def register(request):
    data = request.json
    agent_address = data.pop('agent_address', None)
    if not agent_address:
        # Try to find agent's IP
        x_real_ip = request.headers.get("X-Real-IP")
        agent_address = x_real_ip or request.remote_ip

    data['new_agent_address'] = agent_address
    data['new_agent_port'] = data.pop('agent_port', None)
    create_instance_helper(request.db_session, data)
    return {"message": "OK"}
