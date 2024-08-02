from flask import abort, g, jsonify, render_template, request
from flask import current_app as app

from ...application import send_mail, send_sms
from ...model import orm
from ..flask import admin_required


@app.route("/settings/instances")
@admin_required
def settings_instances():
    return render_template(
        "settings/instances.html",
        sidebar=True,
        instance_list=orm.Instance.all().with_session(g.db_session).all(),
    )


@app.route("/settings/environments")
@admin_required
def settings_environments():
    return render_template(
        "settings/environments.html",
        sidebar=True,
        environments=orm.Environment.all().with_session(g.db_session).all(),
    )


@app.route("/settings/environments/<name>/members")
@admin_required
def settings_environment_members(name):
    return render_template("settings/members.html", sidebar=True, environment=name)


@app.route("/settings/users")
@admin_required
def settings_users():
    return render_template(
        "settings/users.html",
        sidebar=True,
        role_list=orm.Role.all().with_session(g.db_session).all(),
    )


@app.route("/settings/notifications")
@admin_required
def settings_notifications():
    return render_template(
        "settings/notifications.html",
        sidebar=True,
        email_configured=app.temboard.config.notifications.smtp_host,
        sms_configured=app.temboard.config.notifications.twilio_account_sid,
    )


@app.route("/json/test_email", methods=["POST"])
@admin_required
def post_test_email():
    email = request.json.get("email")
    if not email:
        abort(400, "Email field is missing.")

    notifications_conf = app.temboard.config.notifications

    if not notifications_conf.smtp_host:
        abort(406, "SMTP server is not configured")

    send_mail(
        notifications_conf.smtp_host,
        notifications_conf.smtp_port,
        "temBoard notification test",
        "This is a test",
        email,
        notifications_conf.smtp_tls,
        notifications_conf.smtp_login,
        notifications_conf.smtp_password,
        notifications_conf.smtp_from_addr,
    )
    return jsonify({"message": "OK"})


@app.route("/json/test_sms", methods=["POST"])
@admin_required
def post_test_sms():
    phone = request.json.get("phone")
    if not phone:
        abort(400, "Phone field is missing.")

    send_sms(app.temboard.config.notifications, "temBoard notification test", [phone])
    return jsonify({"message": "OK"})
