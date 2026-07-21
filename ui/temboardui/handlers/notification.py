from flask import current_app, g, render_template

from ..web.flask import instance_routes


@instance_routes.route("/notifications")
def notifications():
    notifications = current_app.instance.request("/notifications").json()
    current_app.instance.fetch_status()
    return render_template(
        "notifications.html",
        instance=g.instance,
        notifications=notifications,
        plugin="notifications",
        role=g.current_user,
    )
