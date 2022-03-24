import logging

from temboardui.web import (
    HTTPError,
    admin_required,
    app,
    render_template,
)

from temboardui.application import (
    get_group_list,
    get_group,
    check_group_name,
    check_group_description,
    delete_role_group_from_instance_group,
    update_group,
    add_group,
    add_role_group_in_instance_group,
    delete_group,
)


logger = logging.getLogger(__name__)
PREFIX = r'/json/settings'


@app.route(PREFIX + r'/all/group/(role|instance)$')
@admin_required
def all_group(request, kind):
    groups = get_group_list(request.db_session, kind)
    return {
        'groups': [{
            'name': group.group_name,
            'kind': group.group_kind,
            'description': group.group_description
        } for group in groups],
        'loaded_plugins': request.handler.application.loaded_plugins,
    }


@app.route(
    PREFIX + r"/group/(role|instance)(?:/([0-9a-z\-_\.]{3,16}))?$",
    methods=['GET', 'POST'])
@admin_required
def group(request, kind, name):
    if 'GET' == request.method:
        if not name:
            raise HTTPError(404)
        group = get_group(request.db_session, name, kind)
        data = dict(
            name=group.group_name,
            kind=kind,
            description=group.group_description,
        )
        if kind == 'instance':
            data['user_groups'] = [
                dict(name=g.group_name, description=g.group_description)
                for g in get_group_list(request.db_session)
            ]
            data['in_groups'] = [a.role_group_name for a in group.ari]
        return data
    else:  # POST
        data = request.json
        if not data.get('new_group_name'):
            raise HTTPError(400, "Missing group name.")
        check_group_name(data['new_group_name'])
        if not data.get('description'):
            raise HTTPError(400, "Missing description")
        check_group_description(data['description'])

        if name:  # Group update
            group = get_group(request.db_session, name, kind)
            if 'instance' == kind:
                for ari in group.ari:
                    delete_role_group_from_instance_group(
                        request.db_session, ari.role_group_name,
                        group.group_name)

            group = update_group(
                request.db_session,
                group.group_name, kind,
                data['new_group_name'], data['description'])
        else:  # Group creation
            group = add_group(
                request.db_session,
                data['new_group_name'], data['description'],
                kind)

        if 'user_groups' in data and data['user_groups']:
            for group_name in data['user_groups']:
                add_role_group_in_instance_group(
                    request.db_session, group_name, group.group_name)

        return {'ok': True}


@app.route(PREFIX + r"/delete/group/(role|instance)", methods=['POST'])
@admin_required
def delete_group_handler(request, kind):
    name = request.json.get('group_name')
    if not name:
        raise HTTPError(400)
    delete_group(request.db_session, name, kind)
    return {'delete': True}


@app.route(r"/settings/groups/(role|instance)")
@admin_required
def groups(request, kind):
    return render_template(
        "settings/group.html",
        nav=True, role=request.current_user,
        group_kind=kind,
        group_list=get_group_list(request.db_session, kind),
    )
