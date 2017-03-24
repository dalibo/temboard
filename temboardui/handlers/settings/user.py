import tornado.web
import json

from temboardui.handlers.base import BaseHandler, JsonHandler
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.application import (
    add_role,
    add_role_in_group,
    check_role_email,
    check_role_name,
    check_role_password,
    delete_role,
    delete_role_from_group,
    get_group_list,
    get_groups_by_role,
    get_role,
    get_role_list,
    hash_password,
    update_role,
)
from temboardui.errors import TemboardUIError


class SettingsUserJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, username=None):
        if username is None:
            self.logger.error("Username is missing.")
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({'error': "Username is missing."}))
            self.finish()
        else:
            run_background(self.get_role, self.async_callback, (username,))

    @tornado.web.asynchronous
    def post(self, username=None):
        run_background(self.post_role, self.async_callback, (username,))

    def get_role(self, username):
        try:
            self.logger.info("Getting role by name.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            role = get_role(self.db_session, username)
            groups = get_group_list(self.db_session)

            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return JSONAsyncResult(
                200,
                {
                    'role_name': role.role_name,
                    'role_email': role.role_email,
                    'is_active': role.is_active,
                    'is_admin': role.is_admin,
                    'in_groups': [group.group_name for group in role.groups],
                    'groups': [{
                        'name': group.group_name,
                        'description': group.group_description
                    } for group in groups]
                }
            )
        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, TemboardUIError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})

    def post_role(self, username):
        try:
            self.logger.info("Posting role.")
            role = None
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()
            if username:
                # Update role case.
                role = get_role(self.db_session, username)

            data = tornado.escape.json_decode(self.request.body)
            self.logger.debug(data)

            # Submited attributes checking.
            if 'new_username' not in data or data['new_username'] == '':
                raise TemboardUIError(400, "Username is missing.")
            if 'email' not in data or data['email'] == '':
                raise TemboardUIError(400, "Email is missing.")
            if 'groups' not in data:
                raise TemboardUIError(400, "Groups field is missing.")
            if 'is_active' not in data:
                raise TemboardUIError(400, "Active field is missing.")
            if 'is_admin' not in data:
                raise TemboardUIError(400, "Administrator field is missing.")

            if role and role.role_name != data['new_username']:
                if 'password' not in data or data['password'] == '':
                    raise TemboardUIError(
                        400, "Username will be changed, you need to change "
                        "the password too.")
            if role is None:
                if 'password' not in data or data['password'] == '':
                    raise TemboardUIError(400, "Password is missing.")
            if ('password' in data and data['password'] != '') and \
               ('password2' not in data or data['password2'] == ''):
                raise TemboardUIError(400, "Password confirmation is missing.")
            if 'password' in data and 'password2' in data:
                if data['password'] != data['password2']:
                    raise TemboardUIError(
                        400, "Password confirmation can not be checked.")
            if data['groups'] is not None and type(data['groups']) != list:
                raise TemboardUIError(400, "Invalid group list.")

            check_role_name(data['new_username'])
            check_role_email(data['email'])
            if data['password']:
                check_role_password(data['password'])
                h_passwd = hash_password(data['new_username'],
                                         data['password'])
            else:
                h_passwd = None

            # At this point we can proceed with DB operations.
            # Update role case.
            if role:
                # First step is to remove user from the groups he belongs to.
                role_groups = get_groups_by_role(self.db_session,
                                                 role.role_name)
                if role_groups:
                    for role_group in role_groups:
                        delete_role_from_group(self.db_session, role.role_name,
                                               role_group.group_name)
                role = update_role(
                    self.db_session,
                    role.role_name,
                    data['new_username'],
                    h_passwd,
                    data['email'],
                    data['is_active'],
                    data['is_admin'])
            # New role case.
            else:
                role = add_role(
                    self.db_session,
                    data['new_username'],
                    h_passwd,
                    data['email'],
                    data['is_active'],
                    data['is_admin'])

            # Add user into the new groups.
            if data['groups']:
                for group_name in data['groups']:
                    add_role_in_group(self.db_session, role.role_name,
                                      group_name)

            self.db_session.commit()
            self.logger.info("Done.")
            return JSONAsyncResult(200, {'ok': True})

        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Done.")
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, TemboardUIError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})


class SettingsDeleteUserJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def post(self):
        run_background(self.delete_role, self.async_callback)

    def delete_role(self):
        try:
            self.logger.info("Deleting role.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            data = tornado.escape.json_decode(self.request.body)
            self.logger.debug(data)

            if 'username' not in data or data['username'] == '':
                raise TemboardUIError(400, "Username field is missing.")
            delete_role(self.db_session, data['username'])
            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return JSONAsyncResult(200, {'delete': True})

        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, TemboardUIError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})


class SettingsUserHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        run_background(self.get_index, self.async_callback)

    def get_index(self):
        try:
            self.logger.info("Getting user list.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            role_list = get_role_list(self.db_session)
            self.logger.debug(role_list)

            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return HTMLAsyncResult(
                    200,
                    None,
                    {'nav': True, 'role': self.current_user,
                     'role_list': role_list},
                    template_file='settings/user.html')
        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, TemboardUIError):
                if e.code == 302:
                    return HTMLAsyncResult(302, '/login')
                elif e.code == 401:
                    return HTMLAsyncResult(
                            401,
                            None,
                            {'nav': False},
                            template_file='unauthorized.html')
            return HTMLAsyncResult(
                        500,
                        None,
                        {'nav': False, 'error': e.message},
                        template_file='settings/error.html')
