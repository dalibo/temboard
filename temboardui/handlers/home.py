from temboardui.application import (
    get_instance_groups_by_role,
    get_instances_by_role_name,
)
from ..web import (
    Redirect,
    app,
    anonymous_allowed,
    jsonify,
    render_template,
)
from ..plugins.monitoring.alerting import get_highest_state


@app.route('/')
@anonymous_allowed
def index(request):
    return Redirect('/home')


@app.route('/home')
def home(request):
    role = request.current_user

    groups = get_instance_groups_by_role(request.db_session, role.role_name)
    groups = [group for group in groups]

    return render_template(
        'home.html',
        nav=True, role=role,
        groups=groups,
    )


@app.route('/home/instances')
def home_instances(request):
    role = request.current_user

    # get the instances for which current user has access to
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

    # Get availability for all monitored instances
    cur = request.db_session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    sql = """
        SELECT
          distinct(ia.instance_id),
          i.port,
          h.hostname,
          first_value(available) OVER
            (PARTITION BY ia.instance_id ORDER BY datetime desc) AS available
        FROM monitoring.instance_availability AS ia
        JOIN monitoring.instances AS i
        ON i.instance_id = ia.instance_id
        JOIN monitoring.hosts AS h
        ON i.host_id = h.host_id;
    """
    all_availability = request.db_session.execute(sql, {}).fetchall()
    all_availability = {(i.hostname, i.port): i.available
                        for i in all_availability}

    # set instances availability if known
    for instance in instances:
        try:
            available = all_availability.get((instance['hostname'],
                                              instance['pg_port']))
        except KeyError:
            # Instance may not be monitored yet
            # because it has been added recently or monitor plugin is not
            # activated
            available = None
        instance['available'] = available

    sql = """
        WITH states_by_key AS (
            SELECT
                check_id,
                json_agg(json_build_object('key', key, 'state', state))
                  as state_by_key
            FROM monitoring.check_states
            GROUP BY check_id
        )
        SELECT h.hostname, i.port,
        json_agg(
            json_build_object(
                'name', c.name,
                'warning', c.warning,
                'critical', c.critical,
                'description', c.description,
                'enabled', c.enabled,
                'state_by_key', states_by_key.state_by_key
        )) AS checks
        FROM monitoring.checks c
        JOIN states_by_key ON c.check_id = states_by_key.check_id
        JOIN monitoring.instances i
          ON c.host_id = i.host_id AND c.instance_id = i.instance_id
        JOIN monitoring.hosts h ON h.host_id = i.host_id
        GROUP BY 1,2;
    """
    all_checks = request.db_session.execute(sql, {}).fetchall()
    all_checks = {
        (i.hostname, i.port): [{
                'name': check['name'],
                'state': get_highest_state([s['state']
                                            for s in check['state_by_key']]),
                'description': check['description']
            } for check in i.checks]
        for i in all_checks
    }

    # set instances checks if any
    for instance in instances:
        try:
            checks = all_checks[(instance['hostname'], instance['pg_port'])]
        except KeyError:
            # Instance may not be monitored yet
            # because it has been added recently or monitor plugin is not
            # activated
            checks = []
        instance['checks'] = checks

    return jsonify(instances)
