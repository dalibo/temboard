from flask import abort, g, jsonify, render_template, request
from flask import current_app as app

from ...application import send_mail, send_sms
from ...model import orm
from ..flask import admin_required


@app.route("/settings/instances")
@admin_required
def get_instances():
    return render_template(
        "settings/instances.html",
        nav=True,
        vitejs=app.vitejs,
        role=g.current_user,
        instance_list=orm.Instances.all().with_session(g.db_session).all(),
    )


@app.route("/settings/notifications")
@admin_required
def notifications():
    return render_template(
        "settings/notifications.html",
        nav=True,
        role=g.current_user,
        email_configured=app.temboard.config.notifications.smtp_host,
        sms_configured=app.temboard.config.notifications.twilio_account_sid,
        vitejs=app.vitejs,
    )


@app.route("/json/test_email", methods=["POST"])
@admin_required
def send_test_email():
    data = request.json
    email = data.get("email", None)
    if not email:
        abort(400, "Email field is missing.")

    notifications_conf = app.temboard.config.notifications
    smtp_host = notifications_conf.smtp_host
    smtp_port = notifications_conf.smtp_port
    smtp_tls = notifications_conf.smtp_tls
    smtp_login = notifications_conf.smtp_login
    smtp_password = notifications_conf.smtp_password
    smtp_from_addr = notifications_conf.smtp_from_addr

    if not smtp_host:
        abort(500, "SMTP server is not configured")

    send_mail(
        smtp_host,
        smtp_port,
        "temBoard notification test",
        "This is a test",
        email,
        smtp_tls,
        smtp_login,
        smtp_password,
        smtp_from_addr,
    )
    return jsonify({"message": "OK"})


@app.route("/json/test_sms", methods=["POST"])
@admin_required
def send_test_sms(request):
    data = request.json
    phone = data.get("phone", None)
    if not phone:
        abort(400, "Phone field is missing.")

    send_sms(app.temboard.config.notifications, "temBoard notification test", [phone])
    return jsonify({"message": "OK"})
