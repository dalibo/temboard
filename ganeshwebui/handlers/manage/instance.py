import tornado.web
import json
from time import sleep
from sqlalchemy.exc import *

from ganeshwebui.handlers.base import BaseHandler, JsonHandler
from ganeshwebui.async import *
from ganeshwebui.application import *
from ganeshwebui.errors import GaneshError
from ganeshwebui.ganeshdclient import ganeshd_discover, GaneshdError


class ManageInstanceJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        if agent_address is None or agent_port is None:
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            if agent_address is None:
                self.write(json.dumps({'error': "Agent address is missing."}))
            else:
                self.write(json.dumps({'error': "Agent port is missing."}))
            self.finish()
        else:
            run_background(self.get_instance, self.async_callback, (agent_address, agent_port,))

    @tornado.web.asynchronous
    def post(self, agent_address = None, agent_port = None):
        run_background(self.post_instance, self.async_callback, (agent_address, agent_port))

    def get_instance(self, agent_address, agent_port):
        try:
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            instance = get_instance(self.db_session, agent_address, agent_port)
            groups = get_group_list(self.db_session, 'instance');
            if not instance:
                raise GaneshError(404, "Instance entry not found.") 
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            return JSONAsyncResult(
                    200,
                    {
                        'agent_address': instance.agent_address,
                        'agent_port': instance.agent_port,
                        'agent_key': instance.agent_key,
                        'hostname': instance.hostname,
                        'cpu': instance.cpu,
                        'memory_size': instance.memory_size,
                        'pg_port': instance.pg_port,
                        'pg_version': instance.pg_version,
                        'pg_data': instance.pg_data,
                        'in_groups': [group.group_name for group in instance.groups],
                        'groups': [{'name': group.group_name, 'description': group.group_description} for group in groups]
                    }
                )
        except (GaneshError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, GaneshError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})

    def post_instance(self, agent_address, agent_port):
        try:
            instance = None
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()
            if agent_address and agent_port:
                # Update instance case.
                instance = get_instance(self.db_session, agent_address, agent_port)
                if not instance:
                    raise GaneshError(404, "Instance entry not found.") 

            data = tornado.escape.json_decode(self.request.body)

            # Submited attributes checking.
            if 'new_agent_address' not in data or data['new_agent_address'] == '':
                raise GaneshError(400, "Agent address is missing.")
            if 'new_agent_port' not in data or data['new_agent_port'] == '':
                raise GaneshError(400, "Agent port is missing.")
            if 'agent_key' not in data:
                raise GaneshError(400, "Agent key field is missing.")
            if 'hostname' not in data:
                raise GaneshError(400, "Hostname field is missing.")
            if 'cpu' not in data:
                raise GaneshError(400, "CPU field is missing.")
            if 'memory_size' not in data:
                raise GaneshError(400, "Memory size field is missing.")
            if 'pg_port' not in data:
                raise GaneshError(400, "PostgreSQL port field is missing.")
            if 'pg_version' not in data:
                raise GaneshError(400, "PostgreSQL version field is missing.")
            if 'pg_data' not in data:
                raise GaneshError(400, "PostgreSQL data directory field is missing.")
            if 'groups' not in data:
                raise GaneshError(400, "Groups field is missing.")

            if data['groups'] != None and type(data['groups']) != list:
                raise GaneshError(400, "Invalid group list.")
            check_agent_address(data['new_agent_address'])
            check_agent_port(data['new_agent_port'])

            # At this point we can proceed with DB operations.
            # Update instance case.
            if instance:
                # First step is to remove the instance from the groups it belongs to.
                instance_groups = get_groups_by_instance(self.db_session, instance.agent_address, instance.agent_port)
                if instance_groups:
                    for instance_group in instance_groups:
                        delete_instance_from_group(self.db_session, instance.agent_address, instance.agent_port, instance_group.group_name)
                instance = update_instance(self.db_session,
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
                instance = add_instance(self.db_session,
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
                    add_instance_in_group(self.db_session, instance.agent_address, instance.agent_port, group_name)

            self.db_session.commit()
            return JSONAsyncResult(200, {'ok': True})

        except (GaneshError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, GaneshError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})

class ManageDeleteInstanceJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def post(self):
        run_background(self.delete_instance, self.async_callback)

    def delete_instance(self):
        try:
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            data = tornado.escape.json_decode(self.request.body)
            if 'agent_address' not in data or data['agent_address'] == '':
                raise GaneshError(400, "Agent address field is missing.")
            if 'agent_port' not in data or data['agent_port'] == '':
                raise GaneshError(400, "Agent port field is missing.")
            delete_instance(self.db_session, data['agent_address'], data['agent_port'])
            self.db_session.commit()
            self.db_session.close()
            return JSONAsyncResult(200, {'delete': True})

        except (GaneshError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, GaneshError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})

class ManageInstanceHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        run_background(self.get_index, self.async_callback)

    def get_index(self):
        try:
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()

            instance_list = get_instance_list(self.db_session)
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            return HTMLAsyncResult(
                    200,
                    None,
                    {'nav': True , 'role': self.current_user, 'instance_list': instance_list},
                    template_file = 'manage/instance.html')
        except (GaneshError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, GaneshError):
                if e.code == 302:
                    return HTMLAsyncResult(302, '/login')
                elif e.code == 401:
                    return HTMLAsyncResult(
                            401,
                            None,
                            {'nav': False},
                            template_file = 'unauthorized.html')
            return HTMLAsyncResult(
                        500,
                        None,
                        {'nav': False, 'error': e.message},
                        template_file = 'manage/error.html')



class DiscoverInstanceJsonHandler(JsonHandler):

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_discover, self.async_callback, (agent_address, agent_port))

    def get_discover(self, agent_address, agent_port):
        try:
            self.load_auth_cookie()
            self.start_db_session()
            self.check_admin()
            self.db_session.close()

            res = ganeshd_discover(self.ssl_ca_cert_file, agent_address, agent_port)
            return JSONAsyncResult(200, res)

        except (GaneshError, GaneshdError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, GaneshError) or isinstance(e, GaneshdError):
                return JSONAsyncResult(e.code, {'error': e.message})
            else:
                return JSONAsyncResult(500, {'error': "Internal error."})
