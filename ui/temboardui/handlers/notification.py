from ..web import (
    app,
    render_template,
)


@app.instance_route(r"/notifications")
def notifications(request):
    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        agent_username = None
    notifications = request.instance.get("/notifications")
    return render_template(
        'notifications.html',
        agent_username=agent_username,
        instance=request.instance,
        nav=True,
        notifications=notifications,
        plugin='notifications',
        role=request.current_user,
    )
