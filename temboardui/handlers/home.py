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
    groups = get_instance_groups_by_role(request.db_session, role.role_name)
    return render_template(
        'home.html',
        nav=True, role=role, instance_list=instances,
        groups=groups,
    )
