from temboardui.application import get_instances_by_role_name
from ..web import app, render_template, Redirect


@app.route('/home')
def home(request):
    role = request.current_user
    if not role:
        return Redirect('/login')

    instances = get_instances_by_role_name(request.db_session, role.role_name)

    return render_template(
        'home.html',
        nav=True, role=role, instance_list=instances,
    )
