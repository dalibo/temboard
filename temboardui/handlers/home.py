from temboardui.application import (
    get_instance_groups_by_role,
    get_instances_by_role_name,
)
from ..web import (
    Redirect,
    app,
    anonymous_allowed,
    render_template,
)


@app.route('/')
@anonymous_allowed
def index(request):
    return Redirect('/home')


@app.route('/home')
def home(request):
    role = request.current_user
    instances = get_instances_by_role_name(request.db_session, role.role_name)

    instances = [{
        'hostname': instance.hostname,
        'agent_address': instance.agent_address,
        'agent_port': instance.agent_port,
        'pg_data': instance.pg_data,
        'pg_port': instance.pg_port,
        'pg_version': instance.pg_version,
        'pg_version_summary': instance.pg_version_summary,
        'groups': [group.group_name for group in instance.groups],
        'plugins': [plugin.plugin_name for plugin in instance.plugins],
    } for instance in instances]

    groups = get_instance_groups_by_role(request.db_session, role.role_name)
    groups = [group for group in groups]

    return render_template(
        'home.html',
        nav=True, role=role, instance_list=instances,
        groups=groups,
    )
