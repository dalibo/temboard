import tornado.web
import json

from temboardui.handlers.base import BaseHandler, JsonHandler
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.application import (
    get_group_list,
    get_group,
    check_group_name,
    check_group_description,
    delete_role_group_from_instance_group,
    update_group,
    add_group,
    add_role_group_in_instance_group,
    delete_group,
)
from temboardui.errors import TemboardUIError


class SettingsGroupAllJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, group_kind):
        run_background(self.get_all, self.async_callback, (group_kind,))

    def get_all(self, group_kind):
        try:
            self.logger.info("Getting group list.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            groups = get_group_list(self.db_session, group_kind)
            self.logger.debug(groups)

            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return JSONAsyncResult(
                200,
                {
                    'groups': [{
                        'name': group.group_name,
                        'kind': group.group_kind,
                        'description': group.group_description
                    } for group in groups],
                    'loaded_plugins': self.application.loaded_plugins
                }
            )
        except (TemboardUIError, Exception) as e:
            self.logger.info("Failed.")
            self.logger.exception(str(e))
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, TemboardUIError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})


class SettingsGroupJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, group_kind, group_name=None):
        if group_name is None:
            self.logger.error("Group name is missing.")
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({'error': "Group name is missing."}))
            self.finish()
        else:
            run_background(
                self.get_group, self.async_callback, (group_kind, group_name,))

    @tornado.web.asynchronous
    def post(self, group_kind, group_name=None):
        run_background(
            self.post_group, self.async_callback, (group_kind, group_name,))

    def get_group(self, group_kind, group_name):
        try:
            self.logger.info("Getting group by name.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            group = get_group(self.db_session, group_name, group_kind)
            self.logger.debug(group)

            if group_kind == 'role':
                self.db_session.expunge_all()
                self.db_session.commit()
                self.db_session.close()
                self.logger.info("Done")
                return JSONAsyncResult(
                    200,
                    {
                        'name': group.group_name,
                        'kind': group.group_kind,
                        'description': group.group_description
                    }
                )
            else:
                user_groups = get_group_list(self.db_session)
                self.db_session.expunge_all()
                self.db_session.commit()
                self.db_session.close()
                self.logger.info("Done.")
                return JSONAsyncResult(
                    200,
                    {
                        'name': group.group_name,
                        'kind': group.group_kind,
                        'description': group.group_description,
                        'user_groups': [{
                            'name': user_group.group_name,
                            'description': user_group.group_description
                        } for user_group in user_groups],
                        'in_groups': [ari.role_group_name for ari in group.ari]
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

    def post_group(self, group_kind, group_name):
        try:
            self.logger.info("Posting new group.")
            group = None
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()
            if group_name:
                # Update group case.
                group = get_group(self.db_session, group_name, group_kind)

            data = tornado.escape.json_decode(self.request.body)
            self.logger.debug(data)

            # Submited attributes checking.
            if 'new_group_name' not in data or data['new_group_name'] == '':
                raise TemboardUIError(400, "Group name is missing.")
            if 'description' not in data:
                raise TemboardUIError(
                    400, "Group description field is missing.")
            check_group_name(data['new_group_name'])
            check_group_description(data['description'])

            # At this point we can proceed with DB operations.
            # Update group case.
            if group:
                if group_kind == 'instance':
                    for ari in group.ari:
                        delete_role_group_from_instance_group(
                            self.db_session, ari.role_group_name,
                            group.group_name)

                group = update_group(
                    self.db_session,
                    group.group_name,
                    group_kind,
                    data['new_group_name'],
                    data['description'])
            # New group case.
            else:
                group = add_group(
                    self.db_session,
                    data['new_group_name'],
                    data['description'],
                    group_kind)

            if 'user_groups' in data and data['user_groups']:
                for group_name in data['user_groups']:
                    add_role_group_in_instance_group(
                        self.db_session, group_name, group.group_name)

            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return JSONAsyncResult(200, {'ok': True})

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


class SettingsDeleteGroupJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def post(self, group_kind):
        run_background(self.delete_group, self.async_callback, (group_kind,))

    def delete_group(self, group_kind):
        try:
            self.logger.info("Deleting group.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            data = tornado.escape.json_decode(self.request.body)
            self.logger.debug(data)

            if 'group_name' not in data or data['group_name'] == '':
                raise TemboardUIError(400, "Group name field is missing.")
            delete_group(self.db_session, data['group_name'], group_kind)
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


class SettingsGroupHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self, group_kind):
        run_background(self.get_index, self.async_callback, (group_kind,))

    def get_index(self, group_kind):
        try:
            self.logger.info("Group list.")
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            group_list = get_group_list(self.db_session, group_kind)
            self.logger.debug(group_list)

            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return HTMLAsyncResult(
                200,
                None,
                {
                    'nav': True,
                    'role': self.current_user,
                    'group_list': group_list,
                    'group_kind': group_kind
                },
                template_file='settings/group.html'
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
