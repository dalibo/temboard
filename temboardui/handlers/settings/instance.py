import tornado.web
import json

from temboardui.handlers.base import BaseHandler, JsonHandler
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.application import (
    add_instance,
    add_instance_in_group,
    add_instance_plugin,
    check_agent_address,
    check_agent_port,
    delete_instance,
    delete_instance_from_group,
    get_group_list,
    get_groups_by_instance,
    get_instance,
    get_instance_list,
    purge_instance_plugins,
    update_instance,
)
from temboardui.errors import TemboardUIError
from temboardui.temboardclient import temboard_discover


class SettingsInstanceJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        if agent_address is None or agent_port is None:
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            if agent_address is None:
                self.logger.error("Agent address is missing.")
                self.write(json.dumps({'error': "Agent address is missing."}))
            else:
                self.logger.error("Agent port is missing.")
                self.write(json.dumps({'error': "Agent port is missing."}))
            self.finish()
        else:
            run_background(self.get_instance, self.async_callback,
                           (agent_address, agent_port,))

    @tornado.web.asynchronous
    def post(self, agent_address=None, agent_port=None):
        run_background(self.post_instance, self.async_callback,
                       (agent_address, agent_port))

    @JsonHandler.catch_errors
    def get_instance(self, agent_address, agent_port):
        self.logger.info("Getting instance.")
        self.setUp(agent_address, agent_port)

        self.check_admin()

        groups = get_group_list(self.db_session, 'instance')
        self.logger.info("Done.")
        self.tearDown(commit=False)
        return JSONAsyncResult(
            200,
            {
                'agent_address': self.instance.agent_address,
                'agent_port': self.instance.agent_port,
                'agent_key': self.instance.agent_key,
                'hostname': self.instance.hostname,
                'cpu': self.instance.cpu,
                'memory_size': self.instance.memory_size,
                'pg_port': self.instance.pg_port,
                'pg_version': self.instance.pg_version,
                'pg_data': self.instance.pg_data,
                'in_groups': [group.group_name for group
                              in self.instance.groups],
                'enabled_plugins': [plugin.plugin_name for plugin
                                    in self.instance.plugins],
                'groups': [{
                    'name': group.group_name,
                    'description': group.group_description
                } for group in groups],
                'loaded_plugins': self.application.loaded_plugins
            }
        )

    @JsonHandler.catch_errors
    def post_instance(self, agent_address, agent_port):
        self.logger.info("Posting instance.")
        self.setUp()
        instance = None
        self.check_admin()
        if agent_address and agent_port:
            # Update instance case.
            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance entry not found.")

        data = tornado.escape.json_decode(self.request.body)
        self.logger.debug(data)

        # Submited attributes checking.
        if 'new_agent_address' not in data or \
           data['new_agent_address'] == '':
            raise TemboardUIError(
                400, "Agent address is missing.")
        if 'new_agent_port' not in data or data['new_agent_port'] == '':
            raise TemboardUIError(
                400, "Agent port is missing.")
        if 'agent_key' not in data:
            raise TemboardUIError(
                400, "Agent key field is missing.")
        if 'hostname' not in data:
            raise TemboardUIError(
                400, "Hostname field is missing.")
        if 'cpu' not in data:
            raise TemboardUIError(
                400, "CPU field is missing.")
        if 'memory_size' not in data:
            raise TemboardUIError(
                400, "Memory size field is missing.")
        if 'pg_port' not in data:
            raise TemboardUIError(
                400, "PostgreSQL port field is missing.")
        if 'pg_version' not in data:
            raise TemboardUIError(
                400, "PostgreSQL version field is missing.")
        if 'pg_data' not in data:
            raise TemboardUIError(
                400, "PostgreSQL data directory field is missing.")
        if 'groups' not in data:
            raise TemboardUIError(
                400, "Groups field is missing.")
        if data['groups'] is not None and type(data['groups']) != list:
            raise TemboardUIError(
                400, "Invalid group list.")
        check_agent_address(data['new_agent_address'])
        check_agent_port(data['new_agent_port'])

        # At this point we can proceed with DB operations.
        # Update instance case.
        if instance:
            # First step is to remove the instance from the groups it
            # belongs to.
            instance_groups = get_groups_by_instance(
                self.db_session, instance.agent_address,
                instance.agent_port)
            if instance_groups:
                for instance_group in instance_groups:
                    delete_instance_from_group(
                        self.db_session, instance.agent_address,
                        instance.agent_port, instance_group.group_name)
            # Remove plugins
            purge_instance_plugins(
                self.db_session, instance.agent_address,
                instance.agent_port)

            instance = update_instance(
                self.db_session,
                instance.agent_address,
                instance.agent_port,
                data['new_agent_address'],
                data['new_agent_port'],
                data['agent_key'],
                data['hostname'],
                data['cpu'],
                data['memory_size'],
                data['pg_port'],
                data['pg_version'],
                data['pg_data'])
        # New instance case.
        else:
            instance = add_instance(
                self.db_session,
                data['new_agent_address'],
                data['new_agent_port'],
                data['hostname'],
                data['agent_key'],
                data['cpu'],
                data['memory_size'],
                data['pg_port'],
                data['pg_version'],
                data['pg_data'])

        # Add user into the new groups.
        if data['groups']:
            for group_name in data['groups']:
                add_instance_in_group(
                    self.db_session, instance.agent_address,
                    instance.agent_port, group_name)
        # Add each selected plugin.
        if data['plugins']:
            for plugin_name in data['plugins']:
                # 'administration' plugin case: the plugin is not currently
                # implemented on UI side
                if plugin_name != 'administration':
                    if plugin_name in self.application.loaded_plugins:
                        add_instance_plugin(
                            self.db_session, instance.agent_address,
                            instance.agent_port, plugin_name)
                    else:
                        raise TemboardUIError(
                            404, "Unknown plugin %s." % (plugin_name))
        self.tearDown()
        self.logger.info("Done.")
        return JSONAsyncResult(200, {"message": "OK"})


class SettingsDeleteInstanceJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def post(self):
        run_background(self.delete_instance, self.async_callback)

    @JsonHandler.catch_errors
    def delete_instance(self):
        self.logger.info("Deleting instance.")
        self.setUp()
        self.check_admin()

        data = tornado.escape.json_decode(self.request.body)
        self.logger.debug(data)
        if 'agent_address' not in data or data['agent_address'] == '':
            raise TemboardUIError(400, "Agent address field is missing.")
        if 'agent_port' not in data or data['agent_port'] == '':
            raise TemboardUIError(400, "Agent port field is missing.")
        delete_instance(
            self.db_session, data['agent_address'], data['agent_port'])
        self.tearDown()
        self.logger.info("Done.")
        return JSONAsyncResult(200, {'delete': True})


class SettingsInstanceHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        run_background(self.get_index, self.async_callback)

    def get_index(self):
        try:
            self.setUp()
            self.check_admin()

            instance_list = get_instance_list(self.db_session)
            self.tearDown(commit=False)
            return HTMLAsyncResult(
                    200,
                    None,
                    {
                        'nav': True,
                        'role': self.current_user,
                        'instance_list': instance_list
                    },
                    template_file='settings/instance.html')
        except (TemboardUIError, Exception) as e:
            self.logger.error(str(e))
            try:
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


class DiscoverInstanceJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(
            self.get_discover, self.async_callback,
            (agent_address, agent_port))

    @JsonHandler.catch_errors
    def get_discover(self, agent_address, agent_port):
        self.logger.info("Getting discovery.")
        self.setUp()
        self.check_admin()

        res = temboard_discover(self.ssl_ca_cert_file, agent_address,
                                agent_port)
        self.tearDown(commit=False)
        self.logger.info("Done.")
        return JSONAsyncResult(200, res)


class RegisterInstanceJsonHandler(SettingsInstanceJsonHandler):
    @tornado.web.asynchronous
    def post(self):
        run_background(self.post_register, self.async_callback)

    @SettingsInstanceJsonHandler.catch_errors
    def post_register(self,):
        data = tornado.escape.json_decode(self.request.body)
        if 'agent_address' not in data or data['agent_address'] is None:
            # Try to find agent's IP
            x_real_ip = self.request.headers.get("X-Real-IP")
            data['new_agent_address'] = x_real_ip or self.request.remote_ip
        else:
            data['new_agent_address'] = data['agent_address']
        data['new_agent_port'] = data['agent_port']
        self.request.body = tornado.escape.json_encode(data)
        self.logger.debug(data)
        self.logger.debug(self.request.body)
        return self.post_instance(None, None)
