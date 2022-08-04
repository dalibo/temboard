from ..application import (
    get_instance_groups_by_role,
)
from ..web.tornado import (
    app,
    render_template,
)


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
