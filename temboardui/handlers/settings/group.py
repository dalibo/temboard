import logging

import tornado.web
from tornado.escape import json_decode

from temboardui.web import (
    HTTPError,
    admin_required,
    app,
)

from temboardui.handlers.base import BaseHandler
from temboardui.async import (
    HTMLAsyncResult,
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


logger = logging.getLogger(__name__)
PREFIX = r'/json/settings'


@app.route(PREFIX + r'/all/group/(role|instance)$')
@admin_required
def all_group(request, kind):
    groups = get_group_list(request.db_session, kind)
    return {
        'groups': [{
            'name': group.group_name,
            'kind': group.group_kind,
            'description': group.group_description
        } for group in groups],
        'loaded_plugins': request.handler.application.loaded_plugins,
    }


@app.route(
    PREFIX + r"/group/(role|instance)(?:/([0-9a-z\-_\.]{3,16}))?$",
    methods=['GET', 'POST'])
@admin_required
def group(request, kind, name):
    if 'GET' == request.method:
        if not name:
            raise HTTPError(404)
        group = get_group(request.db_session, name, kind)
        data = dict(
            name=group.group_name,
            kind=kind,
            description=group.group_description,
        )
        if kind == 'instance':
            data['user_groups'] = [
                dict(name=g.group_name, description=g.group_description)
                for g in get_group_list(request.db_session)
            ]
            data['in_groups'] = [a.role_group_name for a in group.ari]
        return data
    else:  # POST
        data = json_decode(request.body)
        if not data.get('new_group_name'):
            raise HTTPError(400, "Missing group name.")
        check_group_name(data['new_group_name'])
        if not data.get('description'):
            raise HTTPError(400, "Missing description")
        check_group_description(data['description'])

        if name:  # Group update
            group = get_group(request.db_session, name, kind)
            if 'instance' == kind:
                for ari in group.ari:
                    delete_role_group_from_instance_group(
                        request.db_session, ari.role_group_name,
                        group.group_name)

            group = update_group(
                request.db_session,
                group.group_name, kind,
                data['new_group_name'], data['description'])
        else:  # Group creation
            group = add_group(
                request.db_session,
                data['new_group_name'], data['description'],
                kind)

        if 'user_groups' in data and data['user_groups']:
            for group_name in data['user_groups']:
                add_role_group_in_instance_group(
                    request.db_session, group_name, group.group_name)

        return {'ok': True}


@app.route(PREFIX + r"/delete/group/(role|instance)", methods=['POST'])
@admin_required
def delete_group_handler(request, kind):
    data = json_decode(request.body)
    name = data.get('group_name')
    if not name:
        raise HTTPError(400)
    delete_group(request.db_session, name, kind)
    return {'delete': True}


class SettingsGroupHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self, group_kind):
        run_background(self.get_index, self.async_callback, (group_kind,))

    def get_index(self, group_kind):
        try:
            self.logger.info("Group list.")
            self.setUp()
            self.check_admin()

            group_list = get_group_list(self.db_session, group_kind)
            self.logger.debug(group_list)

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
