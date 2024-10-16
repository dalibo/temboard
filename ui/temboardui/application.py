import base64
import json
import logging
import re
from binascii import hexlify
from email.mime.text import MIMEText
from hashlib import sha512
from smtplib import SMTP, SMTP_SSL
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.orm.exc import NoResultFound

from temboardui.errors import TemboardUIError
from temboardui.model.orm import Instance, Role

logger = logging.getLogger(__name__)

"""
Instances
"""


def get_instance(session, agent_address, agent_port):
    return Instance.get(agent_address, agent_port).with_session(session).first()


"""
Roles
"""


def get_role_by_auth(session, role_name, role_password):
    try:
        role = (
            session.query(Role)
            .filter(Role.role_name == str(role_name), Role.is_active.is_(True))
            .one()
        )
        if role.role_password != str(role_password):
            raise TemboardUIError(
                400, "Wrong user/password: %s/%s" % (role_name, role_password)
            )
        return role
    except NoResultFound:
        raise TemboardUIError(
            400, "Wrong user/password: %s/%s" % (role_name, role_password)
        )


def hash_password(username, password):
    """
    Hash a password with the following formula:
        sha512(password + sha512(username))
    """
    bytes_password = hexlify(password.encode("utf-8"))
    bytes_sha_username = sha512(username.encode("utf-8")).digest()
    hpasswd = sha512(bytes_password + bytes_sha_username).digest()
    return base64.b64encode(hpasswd)


def gen_cookie(username, hash_password):
    """
    Build secure cookie content as a string containing:
        - content length (excluding length itself)
        - role_name
        - 16 first chars of the hash password

    Part of hash password is there for 2 main reasons:

        1/ If the cookie secret key is stolen, the attacker will be able to
        build a valid secure cookie, so in this situation having a
        non-predictibable variable - part of hash password -  wich can be
        checked on server side will render the attack effective less, unless
        if the attacker knows role's password.

        2/ We don't want to see the full hash password stored in a cookie.
    """
    content = f"{username}:{hash_password[:15]}"
    return f"{len(content) + 1}:{content}"


def get_role_by_cookie(session, content):
    p_cookie_content = r"^([0-9]+):([a-z0-9_\-.]{3,16}):([A-Za-z0-9+/]{15})$"
    r_cookie_content = re.compile(p_cookie_content)
    match = r_cookie_content.match(content)
    if match:
        c_length = match.group(1)
        c_role_name = match.group(2)
        c_fp_hash_password = match.group(3)
        if int(c_length) != (len(c_role_name) + len(c_fp_hash_password) + 2):
            raise Exception("Cookie's content is corrupted.")
        try:
            role = (
                session.query(Role)
                .filter(Role.role_name == str(c_role_name), Role.is_active.is_(True))
                .one()
            )
        except (NoResultFound, Exception):
            raise Exception("Role '%s' not found or not active." % (c_role_name))
        if role.role_password[:15] != str(c_fp_hash_password):
            raise Exception("Password sign not correct.")
        return role
    else:
        raise Exception("Cookie content is not valid.")


def send_mail(
    host,
    port,
    subject,
    content,
    emails,
    tls=False,
    login=None,
    password=None,
    from_addr=None,
):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject

    try:
        if tls:
            smtp = SMTP_SSL(host, port)
        else:
            smtp = SMTP(host, port)

        if login and password:
            logger.debug("Authenticating to SMTP server as %s.", login)
            smtp.login(login, password)

        smtp.sendmail(from_addr or "temboard@undefined", emails, msg.as_string())
        smtp.quit()
    except Exception as e:
        raise TemboardUIError(
            500, "Could not send mail; %s\n" "SMTP connection may be misconfigured." % e
        )


def send_sms(config, content, phones):
    sid = config.twilio_account_sid
    token = config.twilio_auth_token
    from_ = config.twilio_from
    uri = "https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json" % sid
    s = base64.b64encode(f"{sid}:{token}")

    errors = []
    for recipient in phones:
        req = Request(url=uri)
        req.add_header("Authorization", "Basic %s" % s)
        data = {"From": from_, "Body": content, "To": recipient}
        req.add_data(urlencode(data))
        try:
            urlopen(req)
        except HTTPError as e:
            response = json.loads(e.read())
            logger.error("Could not send SMS; %s" % response.get("message"))
            errors.append(recipient)
        except Exception as e:
            logger.error("Could not send SMS; %s" % e)
            errors.append(recipient)

    if errors:
        raise TemboardUIError(
            500,
            "Could not send SMS to %s; \n See logs for more information"
            % ", ".join(errors),
        )
