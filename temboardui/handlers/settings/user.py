from temboardui.application import (
    add_role,
    add_role_in_group,
    check_role_email,
    check_role_name,
    check_role_password,
    check_role_phone,
    delete_role,
    delete_role_from_group,
    get_group_list,
    get_groups_by_role,
    get_role,
    get_role_list,
    hash_password,
    update_role,
)
from temboardui.web import (
    HTTPError,
    admin_required,
    app,
    render_template,
)
from temboardui.errors import TemboardUIError


@app.route(r'/settings/users')
@admin_required
def users(request):
    role_list = get_role_list(request.db_session)
    return render_template(
        'settings/user.html',
        nav=True, role=request.current_user,
        role_list=role_list
    )


@app.route(r'/json/settings/user', methods=['POST'])
@admin_required
def create_user(request):
    data = request.json
    validate_user_data(data)

    h_passwd = handle_password(data)
    role = add_role(request.db_session,
                    data['new_username'],
                    h_passwd,
                    data['email'],
                    data['is_active'],
                    data['is_admin'])
    add_user_to_groups(request, data, role)
    return {'message': 'OK'}


@app.route(r"/json/settings/user/([0-9a-z\-_\.]{3,16})$",
           methods=['GET', 'POST'])
@admin_required
def json_user(request, username):
    if 'GET' == request.method:
        if username is None:
            raise HTTPError(500, "Username is missing")
        role = get_role(request.db_session, username)
        groups = get_group_list(request.db_session)

        return {
            'role_name': role.role_name,
            'role_email': role.role_email,
            'role_phone': role.role_phone,
            'is_active': role.is_active,
            'is_admin': role.is_admin,
            'in_groups': [group.group_name for group in role.groups],
            'groups': [{
                'name': group.group_name,
                'description': group.group_description
            } for group in groups]
        }
    elif 'POST' == request.method:  # update
        data = request.json
        role = get_role(request.db_session, username)
        validate_user_data(data, role)

        h_passwd = handle_password(data)

        # First step is to remove user from the groups he belongs to.
        role_groups = get_groups_by_role(request.db_session,
                                         role.role_name)
        if role_groups:
            for role_group in role_groups:
                delete_role_from_group(request.db_session, role.role_name,
                                       role_group.group_name)
        role = update_role(
            request.db_session,
            role.role_name,
            data['new_username'],
            h_passwd,
            data['email'],
            data['is_active'],
            data['is_admin'],
            data['phone'])

        add_user_to_groups(request, data, role)

        return {"message": "OK"}


@app.route(r'/json/settings/delete/user', methods=['POST'])
@admin_required
def delete_user(request):
    data = request.json
    if not data.get('username'):
        raise HTTPError(400, "Username field is missing.")
    delete_role(request.db_session, data['username'])
    return {'delete': True}


def validate_user_data(data, role=None):
    # Submited attributes checking.
    if not data.get('new_username'):
        raise TemboardUIError(400, "Username is missing.")
    if data.get('email'):
        check_role_email(data['email'])
    if data.get('phone'):
        check_role_phone(data['phone'])
    if 'groups' not in data:
        raise TemboardUIError(400, "Groups field is missing.")
    if 'is_active' not in data:
        raise TemboardUIError(400, "Active field is missing.")
    if 'is_admin' not in data:
        raise TemboardUIError(400, "Administrator field is missing.")

    if role and role.role_name != data['new_username']:
        if not data.get('password'):
            raise TemboardUIError(
                400, "Username will be changed, you need to change "
                "the password too.")
    if role is None:
        if not data.get('password'):
            raise TemboardUIError(400, "Password is missing.")
    if data.get('password') and not data.get('password2'):
        raise TemboardUIError(400, "Password confirmation is missing.")
    if 'password' in data and 'password2' in data:
        if data['password'] != data['password2']:
            raise TemboardUIError(
                400, "Password confirmation can not be checked.")
    if data['groups'] is not None and type(data['groups']) != list:
        raise TemboardUIError(400, "Invalid group list.")

    check_role_name(data['new_username'])


def handle_password(data):
    if data['password']:
        check_role_password(data['password'])
        return hash_password(data['new_username'], data['password'])
    return None


def add_user_to_groups(request, data, role):
    if data['groups']:
        for group_name in data['groups']:
            add_role_in_group(request.db_session, role.role_name, group_name)
