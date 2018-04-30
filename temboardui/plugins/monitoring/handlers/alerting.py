import logging
import cStringIO
from dateutil import parser as dt_parser
import json

import tornado.web
import tornado.escape

from temboardui.handlers.base import JsonHandler
from temboardui.plugins.monitoring.model.orm import Check, CheckState
from temboardui.errors import TemboardUIError
from temboardui.application import get_instance
from temboardui.async import run_background, JSONAsyncResult

from ..tools import get_host_id, get_instance_id

logger = logging.getLogger(__name__)


class AlertingJSONHandler(JsonHandler):

    def setup_env(self, address, port):
        # Init and setup env.
        self.instance = None
        self.role = None
        self.host_id = None
        self.instance_id = None

        # Authentication
        self.load_auth_cookie()
        # Start new DB session
        self.start_db_session()

        self.role = self.current_user
        if not self.role:
            raise TemboardUIError(302, "Current role unknown.")

        self.instance = get_instance(self.db_session, address, port)
        if not self.instance:
            raise TemboardUIError(404, "Instance not found.")
        if 'monitoring' not in [plugin.plugin_name
                                for plugin in self.instance.plugins]:
            raise TemboardUIError(408, "Plugin not active.")

        # Find host_id & instance_id
        self.host_id = get_host_id(self.db_session, self.instance.hostname)
        self.instance_id = get_instance_id(self.db_session, self.host_id,
                                           self.instance.pg_port)

    def close_env(self):
        self.db_session.close()

    def handle_exception(self, e, no_error=0):
        # Exception handler aimed to return JSONAsyncResult
        self.logger.exception(str(e))
        try:
            self.close_env()
        except Exception:
            pass
        if no_error == 1:
            return JSONAsyncResult(http_code=200, data=u'')
        else:
            if (isinstance(e, TemboardUIError)):
                http_code = e.code
                message = e.message
            else:
                http_code = 500
                message = "Internal error"
            return JSONAsyncResult(http_code=http_code,
                                   data={'error': message})


class AlertingJSONCheckStatesHandler(AlertingJSONHandler):

    def get_check_states(self, address, port):
        try:
            self.setup_env(address, port)

            query = self.db_session.query(
                        Check.name, CheckState.key, CheckState.state
                    ).filter(
                        Check.host_id == self.host_id,
                        Check.instance_id == self.instance_id,
                        Check.check_id == CheckState.check_id
                    ).order_by(
                        Check.name,
                        CheckState.key
                    )
            data = [{'name': r.name, 'key': r.key, 'state': r.state}
                    for r in query]

            self.close_env()
            return JSONAsyncResult(http_code=200, data=data)

        except Exception as e:
            return self.handle_exception(e)

    @tornado.web.asynchronous
    def get(self, address, port):
        run_background(self.get_check_states, self.async_callback,
                       (address, port))


class AlertingJSONStateChangesHandler(AlertingJSONHandler):

    def get_state_changes(self, address, port, check_name):
        try:
            self.setup_env(address, port)

            # Arguments
            start = self.get_argument('start', default=None)
            end = self.get_argument('end', default=None)
            key = self.get_argument('key', default=None)
            # Return 200 with empty list when an error occurs
            no_error = int(self.get_argument('noerror', default=0))

            start_time = None
            end_time = None
            if start:
                try:
                    start_time = dt_parser.parse(start)
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')
            if end:
                try:
                    end_time = dt_parser.parse(end)
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')

            data_buffer = cStringIO.StringIO()
            cur = self.db_session.connection().connection.cursor()
            cur.execute("SET search_path TO monitoring")
            query = """
            COPY (
                SELECT array_to_json(array_agg(json_build_array(
                    f.datetime, f.state, f.key, f.value, f.warning, f.critical
                ))) FROM get_state_changes(%s, %s, %s, %s, %s, %s) f
            ) TO STDOUT
            """  # noqa
            # build the query
            query = cur.mogrify(query, (self.host_id, self.instance_id,
                                        check_name, key, start_time, end_time))

            cur.copy_expert(query, data_buffer)
            cur.close()
            data = data_buffer.getvalue()
            data_buffer.close()
            try:
                data = json.loads(data)
            except Exception as e:
                logger.exception(str(e))
                logger.debug(data)
                data = []

            self.close_env()
            return JSONAsyncResult(http_code=200, data=data)
        except Exception as e:
            return self.handle_exception(e, no_error=no_error)

    @tornado.web.asynchronous
    def get(self, address, port, check_name):
        run_background(self.get_state_changes, self.async_callback,
                       (address, port, check_name))


class AlertingJSONChecksHandler(AlertingJSONHandler):

    def get_checks(self, address, port):
        try:
            self.setup_env(address, port)

            query = self.db_session.query(Check).filter(
                        Check.host_id == self.host_id,
                        Check.instance_id == self.instance_id,
                    ).order_by(
                        Check.name,
                    )
            data = [{'name': r.name, 'enabled': r.enabled,
                     'warning': r.warning, 'criticial': r.critical,
                     'description': r.description}
                    for r in query]

            self.close_env()
            return JSONAsyncResult(http_code=200, data=data)

        except Exception as e:
            return self.handle_exception(e)

    @tornado.web.asynchronous
    def get(self, address, port):
        run_background(self.get_checks, self.async_callback, (address, port))

    def post_checks(self, address, port):
        try:
            self.setup_env(address, port)

            # POST data reading
            post = tornado.escape.json_decode(self.request.body)
            if 'checks' not in post or type(post.get('checks')) is not list:
                raise TemboardUIError(400, "Post data not valid.")

            for row in post['checks']:
                # Find the check from its name
                check = self.db_session.query(Check).filter(
                            Check.name == unicode(row.get('name')),
                            Check.host_id == self.host_id,
                            Check.instance_id == self.instance_id).first()

                if u'enabled' in row:
                    check.enabled = bool(row.get(u'enabled'))
                if u'warning' in row:
                    warning = row.get(u'warning')
                    if type(warning) not in (int, float):
                        raise TemboardUIError(400, "Post data not valid.")
                    check.warning = warning
                if u'critical' in row:
                    critical = row.get(u'critical')
                    if type(critical) not in (int, float):
                        raise TemboardUIError(400, "Post data not valid.")
                    check.critical = critical
                if u'description' in row:
                    check.description = row.get(u'description')

                self.db_session.merge(check)

            self.db_session.commit()

            self.close_env()
            return JSONAsyncResult(http_code=200, data=dict())

        except Exception as e:
            return self.handle_exception(e)

    @tornado.web.asynchronous
    def post(self, address, port):
        run_background(self.post_checks, self.async_callback, (address, port))


class AlertingJSONCheckChangesHandler(AlertingJSONHandler):

    def get_check_changes(self, address, port, check_name):
        try:
            self.setup_env(address, port)

            # Arguments
            start = self.get_argument('start', default=None)
            end = self.get_argument('end', default=None)
            # Return 200 with empty list when an error occurs
            no_error = int(self.get_argument('noerror', default=0))

            start_time = None
            end_time = None
            if start:
                try:
                    start_time = dt_parser.parse(start)
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')
            if end:
                try:
                    end_time = dt_parser.parse(end)
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')

            data_buffer = cStringIO.StringIO()
            cur = self.db_session.connection().connection.cursor()
            cur.execute("SET search_path TO monitoring")
            query = """
            COPY (
                SELECT array_to_json(array_agg(json_build_array(
                    f.datetime, f.enabled, f.warning, f.critical, f.description
                ))) FROM get_check_changes(%s, %s, %s, %s, %s) f
            ) TO STDOUT
            """  # noqa
            # build the query
            query = cur.mogrify(query, (self.host_id, self.instance_id,
                                        check_name, start_time, end_time))

            cur.copy_expert(query, data_buffer)
            cur.close()
            data = data_buffer.getvalue()
            data_buffer.close()
            try:
                data = json.loads(data)
            except Exception as e:
                logger.exception(str(e))
                logger.debug(data)
                data = []

            self.close_env()
            return JSONAsyncResult(http_code=200, data=data)

        except Exception as e:
            return self.handle_exception(e, no_error=no_error)

    @tornado.web.asynchronous
    def get(self, address, port, check_name):
        run_background(self.get_check_changes, self.async_callback,
                       (address, port, check_name))
