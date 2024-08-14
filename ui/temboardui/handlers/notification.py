from ..web.tornado import app, render_template


@app.instance_route(r"/notifications")
def notifications(request):
    notifications = request.instance.get("/notifications")
    request.instance.fetch_status()
    return render_template(
        "notifications.html",
        instance=request.instance,
        notifications=notifications,
        plugin="notifications",
        role=request.current_user,
    )
