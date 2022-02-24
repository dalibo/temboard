from temboardui.application import (
    send_mail,
    send_sms,
)
from temboardui.web import (
    HTTPError,
    admin_required,
    app,
    render_template,
)


@app.route(r'/settings/notifications')
@admin_required
def notifications(request):
    return render_template(
        'settings/notifications.html',
        nav=True, role=request.current_user,
        email_configured=app.config.notifications.smtp_host,
        sms_configured=app.config.notifications.twilio_account_sid,
    )


@app.route(r'/json/test_email', methods=['POST'])
@admin_required
def send_test_email(request):
    data = request.json
    email = data.get('email', None)
    if not email:
        raise HTTPError(400, "Email field is missing.")

    notifications_conf = app.config.notifications
    smtp_host = notifications_conf.smtp_host
    smtp_port = notifications_conf.smtp_port
    smtp_tls = notifications_conf.smtp_tls
    smtp_login = notifications_conf.smtp_login
    smtp_password = notifications_conf.smtp_password
    smtp_from_addr = notifications_conf.smtp_from_addr

    if not smtp_host:
        raise HTTPError(500, "SMTP server is not configured")

    send_mail(smtp_host, smtp_port, 'temBoard notification test',
              'This is a test', email, smtp_tls, smtp_login, smtp_password,
              smtp_from_addr)
    return {'message': 'OK'}


@app.route(r'/json/test_sms', methods=['POST'])
@admin_required
def send_test_sms(request):
    data = request.json
    phone = data.get('phone', None)
    if not phone:
        raise HTTPError(400, "Phone field is missing.")

    send_sms(app.config.notifications, 'temBoard notification test', [phone])
    return {'message': 'OK'}
