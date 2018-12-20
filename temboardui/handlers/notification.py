from ..web import (
    app,
    render_template,
)


@app.instance_route(r"/notifications")
def notifications(request):
    agent_profile = request.instance.get_profile()
    notifications = request.instance.get("/notifications")
    return render_template(
        'notifications.html',
        agent_username=agent_profile['username'],
        instance=request.instance,
        nav=True,
        notifications=notifications,
        plugin='notifications',
        role=request.current_user,
    )
