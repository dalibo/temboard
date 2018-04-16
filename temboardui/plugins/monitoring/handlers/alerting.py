import logging
import cStringIO
from dateutil import parser as dt_parser

import tornado.web
import tornado.escape

from temboardui.handlers.base import JsonHandler, CsvHandler
from temboardui.plugins.monitoring.model.orm import Check, CheckState
from temboardui.errors import TemboardUIError
from temboardui.application import get_instance
from temboardui.async import run_background, JSONAsyncResult, CSVAsyncResult

from ..tools import get_host_id, get_instance_id

logger = logging.getLogger(__name__)


class AlertingJSONCheckStatesHandler(JsonHandler):

    def get_check_states(self, agent_address, agent_port):
        try:
            data = list()
            instance = None
            role = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if 'monitoring' not in [plugin.plugin_name
                                    for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")

            # Find host_id & instance_id
            host_id = get_host_id(self.db_session, instance.hostname)
            instance_id = get_instance_id(self.db_session, host_id,
                                          instance.pg_port)
            query = self.db_session.query(
                        Check.name, CheckState.key, CheckState.state
                    ).filter(
                        Check.host_id == host_id,
                        Check.instance_id == instance_id,
                        Check.check_id == CheckState.check_id
                    ).order_by(
                        Check.name,
                        CheckState.key
                    )
            data = [{'name': r.name, 'key': r.key, 'state': r.state}
                    for r in query]
            self.db_session.close()
            return JSONAsyncResult(http_code=200, data=data)

        except (TemboardUIError, Exception) as e:
            self.logger.exception(e)
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_check_states, self.async_callback,
                       (agent_address, agent_port))


class AlertingDataCheckResultsHandler(CsvHandler):

    def get_data_check_results(self, address, port, check_name):
        try:
            instance = None
            role = None
            no_error = 0

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, address, port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if 'monitoring' not in [plugin.plugin_name
                                    for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")

            # Find host_id & instance_id
            host_id = get_host_id(self.db_session, instance.hostname)
            instance_id = get_instance_id(self.db_session, host_id,
                                          instance.pg_port)

            self.db_session.expunge_all()

            # Arguments
            start = self.get_argument('start', default=None)
            end = self.get_argument('end', default=None)
            key = self.get_argument('key', default=None)
            # Return 200 with empty list when an error occurs
            no_error = int(self.get_argument('noerror', default=0))
            changes_only = int(self.get_argument('changes_only', default=0))

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
                SELECT datetime, state, key, value, warning, critical
                FROM get_check_results(%s, %s, %s, %s, %s, %s)
                ORDER BY datetime DESC
            ) TO STDOUT WITH CSV HEADER
            """
            if changes_only == 1:
                query = """
                COPY (
                    SELECT sq.datetime, sq.state, sq.key, sq.value, sq.warning,
                           sq.critical
                    FROM (
                        SELECT *, LEAD(state) OVER (ORDER BY datetime DESC)
                            AS prev_state
                        FROM get_check_results(%s, %s, %s, %s, %s, %s)
                    ) AS sq
                    WHERE sq.state IS DISTINCT FROM sq.prev_state
                    ORDER BY sq.datetime DESC
                ) TO STDOUT WITH CSV HEADER
                """
            # build the query
            query = cur.mogrify(query, (host_id, instance_id, check_name, key,
                                start_time, end_time))

            cur.copy_expert(query, data_buffer)
            cur.close()
            data = data_buffer.getvalue()
            data_buffer.close()

            self.db_session.commit()
            self.db_session.close()
            return CSVAsyncResult(http_code=200, data=data)
        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            try:
                self.db_session.close()
            except Exception:
                pass
            if no_error == 1:
                return CSVAsyncResult(http_code=200, data=u'')
            else:
                if (isinstance(e, TemboardUIError)):
                    return CSVAsyncResult(http_code=e.code,
                                          data={'error': e.message})
                else:
                    return CSVAsyncResult(http_code=500,
                                          data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, check_name):
        run_background(self.get_data_check_results, self.async_callback,
                       (agent_address, agent_port, check_name))


class AlertingJSONChecksHandler(JsonHandler):

    def get_checks(self, agent_address, agent_port):
        try:
            data = list()
            instance = None
            role = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if 'monitoring' not in [plugin.plugin_name
                                    for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")

            # Find host_id & instance_id
            host_id = get_host_id(self.db_session, instance.hostname)
            instance_id = get_instance_id(self.db_session, host_id,
                                          instance.pg_port)
            query = self.db_session.query(Check).filter(
                        Check.host_id == host_id,
                        Check.instance_id == instance_id,
                    ).order_by(
                        Check.name,
                    )
            data = [{'name': r.name, 'enabled': r.enabled,
                     'warning': r.threshold_w, 'criticial': r.threshold_c,
                     'description': r.description}
                    for r in query]
            self.db_session.close()
            return JSONAsyncResult(http_code=200, data=data)

        except (TemboardUIError, Exception) as e:
            self.logger.exception(e)
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_checks, self.async_callback,
                       (agent_address, agent_port))

    def post_checks(self, agent_address, agent_port):
        try:
            instance = None
            role = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if 'monitoring' not in [plugin.plugin_name
                                    for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")

            # Find host_id & instance_id
            host_id = get_host_id(self.db_session, instance.hostname)
            instance_id = get_instance_id(self.db_session, host_id,
                                          instance.pg_port)
            # POST data reading
            post = tornado.escape.json_decode(self.request.body)
            if 'checks' not in post or type(post.get('checks')) is not list:
                raise TemboardUIError(400, "Post data not valid.")

            for row in post['checks']:
                # Find the check from its name
                check = self.db_session.query(Check).filter(
                            Check.name == unicode(row.get('name')),
                            Check.host_id == host_id,
                            Check.instance_id == instance_id).first()

                if u'enabled' in row:
                    check.enabled = bool(row.get(u'enabled'))
                if u'warning' in row:
                    warning = row.get(u'warning')
                    if type(warning) not in (int, float):
                        raise TemboardUIError(400, "Post data not valid.")
                    check.threshold_w = warning
                if u'critical' in row:
                    critical = row.get(u'critical')
                    if type(critical) not in (int, float):
                        raise TemboardUIError(400, "Post data not valid.")
                    check.threshold_c = critical
                if u'description' in row:
                    check.description = row.get(u'description')

                self.db_session.merge(check)

            self.db_session.commit()
            self.db_session.close()
            return JSONAsyncResult(http_code=200, data=dict())

        except (TemboardUIError, Exception) as e:
            self.logger.exception(e)
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_checks, self.async_callback,
                       (agent_address, agent_port))
