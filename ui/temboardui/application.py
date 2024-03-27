from binascii import hexlify
from hashlib import sha512
import base64
import json
import logging
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import (
    NoResultFound,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from smtplib import SMTP, SMTP_SSL
from email.mime.text import MIMEText

from temboardui.model.orm import (
    AccessRoleInstance,
    Groups,
    Instances,
    InstanceGroups,
    Plugins,
    Roles,
    RoleGroups,
)
from temboardui.errors import TemboardUIError

logger = logging.getLogger(__name__)

"""
Roles
"""


def add_role(session,
             role_name,
             role_password,
             role_email,
             is_active=True,
             is_admin=False):
    try:
        role = Roles(
            role_name=str(role_name),
            role_password=str(role_password),
            role_email=str(role_email),
            is_active=is_active,
            is_admin=is_admin)
        session.add(role)
        session.flush()
        return role
    except IntegrityError as e:
        if str(e).find('roles_role_email_key') > 0:
            raise TemboardUIError(400, "Email address '%s' already in use." %
                                  (role_email))
        elif str(e).find('roles_pkey') > 0:
            raise TemboardUIError(400,
                                  "Role '%s' already exists." % (role_name))


def update_role(session,
                role_name,
                new_role_name=None,
                role_password=None,
                role_email=None,
                is_active=None,
                is_admin=None,
                role_phone=None):
    try:
        role = session.query(Roles) \
            .filter_by(role_name=str(role_name)) \
            .first()
        if new_role_name is not None:
            role.role_name = str(new_role_name)
        if role_password is not None:
            role.role_password = str(role_password)
        if role_email is not None:
            role.role_email = str(role_email)
        if role_phone is not None:
            role.role_phone = str(role_phone) if role_phone else None
        if is_active is not None:
            role.is_active = is_active
        if is_admin is not None:
            role.is_admin = is_admin
        session.merge(role)
        session.flush()
        return role
    except IntegrityError as e:
        if str(e).find('roles_role_email_key') > 0:
            raise TemboardUIError(400, "Email address '%s' already in use." %
                                  (role_email))
        elif str(e).find('roles_pkey') > 0:
            raise TemboardUIError(400, "Role '%s' already exists." %
                                  (new_role_name))
        else:
            raise
    except AttributeError:
        raise TemboardUIError(400, "Role '%s' not found." % (role_name))


def get_role(session, role_name):
    try:
        return session.query(Roles).options(
            joinedload(Roles.groups)).filter_by(
                role_name=str(role_name)).first()
    except AttributeError:
        raise TemboardUIError(400, "Role '%s' not found." % (role_name))


def delete_role(session, role_name):
    try:
        role = session.query(Roles).filter(
            Roles.role_name == str(role_name)).one()
        session.delete(role)
    except NoResultFound:
        raise TemboardUIError(400, "Role '%s' not found." % (role_name))


def get_role_list(
        session, ):
    return session.query(Roles).options(joinedload(Roles.groups)).order_by(
        Roles.role_name).all()


"""
Groups
"""


def add_group(session, group_name, group_description, group_kind):
    try:
        group = Groups(
            group_name=str(group_name),
            group_description=str(group_description),
            group_kind=str(group_kind))
        session.add(group)
        session.flush()
        return group
    except IntegrityError as e:
        if str(e).find('groups_group_kind_check') > 0:
            raise TemboardUIError(400, "Group kind '%s' does not exist." %
                                  (group_kind))
        elif str(e).find('groups_pkey') > 0:
            raise TemboardUIError(400, "Group '%s' ('%s') already exists." %
                                  (group_name, group_kind))
        else:
            raise


def get_group(session, group_name, group_kind):
    try:
        if group_kind == 'role':
            return session.query(Groups).filter_by(
                group_name=str(group_name),
                group_kind=str(group_kind)).one()
        else:
            return session.query(Groups).options(
                joinedload(Groups.ari)).filter(
                    Groups.group_name == str(group_name),
                    Groups.group_kind == str(group_kind)).one()
    except AttributeError:
        raise TemboardUIError(
            400,
            f"Group '{group_name}' ({group_kind}) not found.",
        )


def update_group(session,
                 group_name,
                 group_kind,
                 new_group_name=None,
                 group_description=None):
    try:
        group = session.query(Groups) \
            .filter_by(
                group_name=str(group_name),
                group_kind=str(group_kind)) \
            .first()
        if new_group_name is not None:
            group.group_name = str(new_group_name)
        if group_description is not None:
            group.group_description = str(group_description)
        session.merge(group)
        session.flush()
        return group
    except IntegrityError as e:
        if str(e).find('groups_pkey') > 0:
            raise TemboardUIError(400, "Group name '%s' already in use." %
                                  (new_group_name))
        else:
            raise
    except AttributeError:
        raise TemboardUIError(400, "Group '%s' ('%s') not found." %
                              (group_name, group_kind))


def delete_group(session, group_name, group_kind):
    try:
        group = session.query(Groups).filter(
            Groups.group_name == str(group_name),
            Groups.group_kind == str(group_kind)).one()
        session.delete(group)
    except NoResultFound:
        raise TemboardUIError(400, "Group '%s' not found." % (group_name))


def get_group_list(session, group_kind='role'):
    if group_kind == 'role':
        return session.query(Groups).filter(
            Groups.group_kind == str(group_kind)).order_by(
                Groups.group_name).all()
    else:
        return session.query(Groups).options(joinedload(Groups.ari)).filter(
            Groups.group_kind == str(group_kind)).order_by(
                Groups.group_name).all()


def add_role_in_group(session, role_name, group_name):
    try:
        role_group = RoleGroups(
            role_name=str(role_name), group_name=str(group_name))
        session.add(role_group)
        session.flush()
    except IntegrityError as e:
        if str(e).find('role_groups_group_name_fkey') > 0:
            raise TemboardUIError(400, "Group '%s' ('role') does not exist." %
                                  (group_name))
        elif str(e).find('role_groups_role_name_fkey') > 0:
            raise TemboardUIError(400,
                                  "Role '%s' does not exist." % (role_name))
        elif str(e).find('role_groups_pkey') > 0:
            raise TemboardUIError(400, "Role '%s' already in group '%s'." %
                                  (role_name, group_name))
        else:
            raise TemboardUIError(400, str(e))


def delete_role_from_group(session, role_name, group_name):
    try:
        role_group = session.query(RoleGroups).filter(
            RoleGroups.group_name == str(group_name),
            RoleGroups.role_name == str(role_name)).one()
        session.delete(role_group)
    except NoResultFound:
        raise TemboardUIError(400, "Role '%s' not found in group '%s'." %
                              (role_name, group_name))


def get_groups_by_role(session, role_name):
    return session.query(RoleGroups).filter(
        RoleGroups.role_name == str(role_name)).order_by(
            RoleGroups.group_name).all()


def get_instance_groups_by_role(session, role_name):
    return session.query(InstanceGroups.group_name).filter(
        InstanceGroups.group_name == AccessRoleInstance.instance_group_name,
        AccessRoleInstance.role_group_name == RoleGroups.group_name,
        RoleGroups.role_name == str(role_name)).group_by(
            InstanceGroups.group_name).order_by(
                InstanceGroups.group_name).all()


"""
Instances
"""


def add_instance(session,
                 new_agent_address,
                 new_agent_port,
                 **kw):
    try:
        instance = Instances.factory(
            agent_address=str(new_agent_address),
            agent_port=int(new_agent_port),
            **kw
        )
        session.add(instance)
        session.flush()
        return instance
    except IntegrityError as e:
        if 'instances_pkey' in str(e):
            raise TemboardUIError(400,
                                  "Instance entry ('%s:%s') already exists." %
                                  (new_agent_address, new_agent_port))
        else:
            raise


def get_instance(session, agent_address, agent_port):
    return (
        Instances.get(agent_address, agent_port)
        .with_session(session)
        .first()
    )


def delete_instance(session, agent_address, agent_port):
    from temboardui.plugins.monitoring.model.orm import (
        Host as MonitoringHost,
        Instance as MonitoringInstance,
    )

    try:
        instance = session.query(Instances).filter(
            Instances.agent_address == str(agent_address),
            Instances.agent_port == agent_port).one()
        session.delete(instance)
    except NoResultFound:
        raise TemboardUIError(400, "Instance entry ('%s:%s') not found." %
                              (agent_address, agent_port))

    # Also delete any monitoring data
    # First all instance data
    try:
        monitoring_instance = session.query(MonitoringInstance) \
            .join(MonitoringHost) \
            .filter(
                MonitoringHost.hostname == instance.hostname,
                MonitoringInstance.port == instance.pg_port).one()
        session.delete(monitoring_instance)
    except NoResultFound:
        pass

    # Then delete host data if there's no instance left referenced for this
    # host
    count = session.query(MonitoringInstance.instance_id) \
        .join(MonitoringHost) \
        .filter(MonitoringHost.hostname == instance.hostname) \
        .count()
    if count == 0:
        # Using bulk delete query here to prevent errors on not null constraint
        # on checks::host_id column (ON CASCADE DELETE not working)
        # when using session.delete(host)
        try:
            session.query(MonitoringHost) \
                .filter(MonitoringHost.hostname == instance.hostname) \
                .delete()
        except NoResultFound:
            pass
        except Exception as e:
            raise TemboardUIError(400, str(e))


def add_instance_in_group(session, agent_address, agent_port, group_name):
    try:
        # Create instance group if not exists
        group = Groups(group_name=str(group_name), group_kind='instance')
        session.merge(group)
        session.flush()

        instance_group = InstanceGroups(
            agent_address=str(agent_address),
            agent_port=agent_port,
            group_name=str(group_name))
        session.add(instance_group)
        session.flush()
    except IntegrityError as e:
        if str(e).find('instance_groups_group_name_fkey') > 0:
            raise TemboardUIError(
                400, "Group '%s' ('instance') does not exist." % (group_name))
        elif str(e).find('instance_groups_agent_address_fkey') > 0:
            raise TemboardUIError(400,
                                  "Instance entry ('%s:%s') does not exist." %
                                  (agent_address, agent_port))
        elif str(e).find('instance_groups_pkey') > 0:
            raise TemboardUIError(
                400, "Instance entry ('%s:%s)' already in group '%s'." %
                (agent_address, agent_port, group_name))
        else:
            raise TemboardUIError(400, str(e))


def purge_instance_plugins(session, agent_address, agent_port):
    try:
        plugins = session.query(Plugins).filter(
            Plugins.agent_address == str(agent_address),
            Plugins.agent_port == agent_port).all()
        for plugin in plugins:
            session.delete(plugin)
    except Exception as e:
        raise TemboardUIError(400, str(e))


def add_instance_plugin(session, agent_address, agent_port, plugin_name):
    try:
        plugin = Plugins(
            agent_address=str(agent_address),
            agent_port=agent_port,
            plugin_name=str(plugin_name))
        session.add(plugin)
        session.flush()
    except IntegrityError as e:
        if str(e).find('plugins_pkey') > 0:
            raise TemboardUIError(
                400, "Plugin '%s' was already activated for this instance." %
                (plugin_name))
        elif str(e).find('plugins_agent_address_fkey') > 0:
            raise TemboardUIError(400, "Instance '%s:%s' does not exist." %
                                  (agent_address, agent_port))
        else:
            raise


def get_instance_list(
        session, ):
    return session.query(Instances).options(
        joinedload(Instances.groups),
        joinedload(Instances.plugins)).order_by(Instances.hostname).all()


def delete_instance_from_group(session, agent_address, agent_port, group_name):
    try:
        instance_group = session.query(InstanceGroups).filter(
            InstanceGroups.agent_address == str(agent_address),
            InstanceGroups.agent_port == agent_port,
            InstanceGroups.group_name == str(group_name)).one()
        session.delete(instance_group)
    except NoResultFound:
        raise TemboardUIError(
            400, "Instance entry ('%s:%s)' not found in group '%s'." %
            (agent_address, agent_port, group_name))


def get_groups_by_instance(session, agent_address, agent_port):
    return session.query(InstanceGroups).filter(
        InstanceGroups.agent_address == str(agent_address),
        InstanceGroups.agent_port == agent_port).order_by(
            InstanceGroups.group_name).all()


def get_roles_by_instance(session, agent_address, agent_port):
    return session.query(Roles) \
        .filter(
            AccessRoleInstance.role_group_name == RoleGroups.group_name,
            AccessRoleInstance.instance_group_name ==
            InstanceGroups.group_name,
            Instances.agent_address == agent_address,
            Instances.agent_port == agent_port,
            RoleGroups.role_name == Roles.role_name,
            InstanceGroups.agent_address == agent_address,
            InstanceGroups.agent_port == agent_port,
        )


def add_role_group_in_instance_group(session, role_group_name,
                                     instance_group_name):
    try:
        ari = AccessRoleInstance(
            role_group_name=str(role_group_name),
            instance_group_name=str(instance_group_name))
        session.add(ari)
        session.flush()
    except IntegrityError as e:
        if str(e).find('access_role_instance_pkey') > 0:
            raise TemboardUIError(
                400, "Group '%s' ('role') has already access to '%s'." %
                (role_group_name, instance_group_name))
        elif str(e).find(
                'access_role_instance_instance_group_name_fkey') > 0:
            raise TemboardUIError(400, "Instance group '%s' does not exist." %
                                  (instance_group_name))
        elif str(e).find('access_role_instance_role_group_name_fkey') > 0:
            raise TemboardUIError(400, "Role group '%s' does not exist." %
                                  (role_group_name))
        else:
            raise


def delete_role_group_from_instance_group(session, role_group_name,
                                          instance_group_name):
    try:
        ari = session.query(AccessRoleInstance).filter(
            AccessRoleInstance.role_group_name == str(role_group_name),
            AccessRoleInstance.instance_group_name == str(
                instance_group_name)).one()
        session.delete(ari)
    except NoResultFound:
        raise TemboardUIError(
            400, "Role group '%s' not found in instance group '%s'." %
            (role_group_name, instance_group_name))


def get_instances_by_role_name(session, role_name):
    return session.query(Instances).filter(
            Instances.agent_address == InstanceGroups.agent_address,
            Instances.agent_port == InstanceGroups.agent_port,
            InstanceGroups.group_name ==
            AccessRoleInstance.instance_group_name,
            AccessRoleInstance.role_group_name == RoleGroups.group_name,
            RoleGroups.role_name == str(role_name)).order_by(
                InstanceGroups.group_name, Instances.agent_address)


def get_role_by_auth(session, role_name, role_password):
    try:
        role = session.query(Roles).filter(
            Roles.role_name == str(role_name),
            Roles.is_active.is_(True)).one()
        if role.role_password != str(role_password):
            raise TemboardUIError(400, "Wrong user/password: %s/%s" %
                                  (role_name, role_password))
        return role
    except NoResultFound:
        raise TemboardUIError(400, "Wrong user/password: %s/%s" %
                              (role_name, role_password))


def hash_password(username, password):
    """
    Hash a password with the following formula:
        sha512(password + sha512(username))
    """
    bytes_password = hexlify(password.encode('utf-8'))
    bytes_sha_username = sha512(username.encode('utf-8')).digest()
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
    p_cookie_content = r'^([0-9]+):([a-z0-9_\-.]{3,16}):([A-Za-z0-9+/]{15})$'
    r_cookie_content = re.compile(p_cookie_content)
    match = r_cookie_content.match(content)
    if match:
        c_length = match.group(1)
        c_role_name = match.group(2)
        c_fp_hash_password = match.group(3)
        if int(c_length) != (len(c_role_name) + len(c_fp_hash_password) + 2):
            raise Exception("Cookie's content is corrupted.")
        try:
            role = session.query(Roles).filter(
                Roles.role_name == str(c_role_name),
                Roles.is_active.is_(True)).one()
        except (NoResultFound, Exception):
            raise Exception("Role '%s' not found or not active." %
                            (c_role_name))
        if role.role_password[:15] != str(c_fp_hash_password):
            raise Exception("Password sign not correct.")
        return role
    else:
        raise Exception("Cookie content is not valid.")


_reserved_role_name = [
    'temboard',
]


def check_role_name(role_name):
    p_role_name = r'^([a-z0-9_\-.]{3,16})$'
    r_role_name = re.compile(p_role_name)
    if not r_role_name.match(role_name):
        raise TemboardUIError(
            400, "Invalid username, must satisfy this regexp pattern: %s" %
            (p_role_name))

    if role_name in _reserved_role_name:
        raise TemboardUIError(400, "Reserved role name")


def check_role_email(role_email):
    p_role_email = r'^([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)$'
    r_role_email = re.compile(p_role_email)
    if not r_role_email.match(role_email):
        raise TemboardUIError(400, "Invalid email address.")


def check_role_password(role_password):
    p_role_password = r'^(.{8,})$'
    r_role_password = re.compile(p_role_password)
    if not r_role_password.match(role_password):
        raise TemboardUIError(
            400, "Invalid password, it must contain at least 8 char.")


def check_role_phone(role_phone):
    p_role_phone = r'^[+][0-9]+$'
    r_role_phone = re.compile(p_role_phone)
    if not r_role_phone.match(role_phone):
        raise TemboardUIError(400, "Phone must look like +14155552671")


def check_group_name(group_name):
    p_group_name = r'^([a-z0-9_\-.]{3,16})$'
    r_group_name = re.compile(p_group_name)
    if not r_group_name.match(group_name):
        raise TemboardUIError(
            400, "Invalid group name, must satisfy this regexp pattern: %s" %
            (p_group_name))


def check_group_description(group_description):
    if len(group_description) > 255:
        raise TemboardUIError(
            400,
            "Invalid group description, must be a 256 char (max) length "
            "string."
        )


def check_agent_address(value):
    p_check = r'^([0-9a-zA-Z\-\._:]+)$'
    r_check = re.compile(p_check)
    if not r_check.match(value):
        raise TemboardUIError(400, "Invalid agent address.")


def check_agent_port(value):
    p_check = r'^([0-9]{1,5})$'
    r_check = re.compile(p_check)
    if not r_check.match(value):
        raise TemboardUIError(400, "Invalid agent port.")


def send_mail(host, port, subject, content, emails, tls=False, login=None,
              password=None, from_addr=None):

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = subject

    try:
        if tls:
            smtp = SMTP_SSL(host, port)
        else:
            smtp = SMTP(host, port)

        if login and password:
            logger.debug("Authenticating to SMTP server as %s.", login)
            smtp.login(login, password)

        smtp.sendmail(from_addr, emails, msg.as_string())
        smtp.quit()
    except Exception as e:
        raise TemboardUIError(
            500,
            "Could not send mail; %s\n"
            "SMTP connection may be misconfigured." % e)


def send_sms(config, content, phones):
    sid = config.twilio_account_sid
    token = config.twilio_auth_token
    from_ = config.twilio_from
    uri = 'https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json' % sid
    s = base64.b64encode(f'{sid}:{token}')

    errors = []
    for recipient in phones:
        req = Request(url=uri)
        req.add_header('Authorization', 'Basic %s' % s)
        data = {'From': from_, 'Body': content, 'To': recipient}
        req.add_data(urlencode(data))
        try:
            urlopen(req)
        except HTTPError as e:
            response = json.loads(e.read())
            logger.error("Could not send SMS; %s" % response.get('message'))
            errors.append(recipient)
        except Exception as e:
            logger.error("Could not send SMS; %s" % e)
            errors.append(recipient)

    if errors:
        raise TemboardUIError(
            500,
            "Could not send SMS to %s; \n See logs for more information" %
            ', '.join(errors))
