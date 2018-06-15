import logging
import cStringIO
from dateutil import parser as dt_parser
from datetime import datetime
import json

import tornado.web
import tornado.escape

from temboardui.handlers.base import (
    BaseHandler,
    JsonHandler,
)
from temboardui.temboardclient import TemboardError, temboard_profile
from temboardui.plugins.monitoring.model.orm import (
    Check,
    CheckState,
)
from temboardui.errors import TemboardUIError
from temboardui.async import (
    run_background,
    HTMLAsyncResult,
    JSONAsyncResult,
)

from ..tools import get_host_id, get_instance_id
from ..alerting import checks_info, check_state_detail, check_specs


logger = logging.getLogger(__name__)


class AlertingHTMLHandler(BaseHandler):

    @BaseHandler.catch_errors
    def get_index(self, agent_address, agent_port):
        self.setUp(agent_address, agent_port)
        xsession = self.get_secure_cookie(
            "temboard_%s_%s" % (agent_address, agent_port))

        # Here we want to get the current agent username if a session
        # already exists.
        # Monitoring plugin doesn't require agent authentication since we
        # already have the data.
        # Don't fail if there's a session error (for example when the agent
        # has been restarted)
        agent_username = None
        try:
            if xsession:
                data_profile = temboard_profile(self.ssl_ca_cert_file,
                                                agent_address,
                                                agent_port,
                                                xsession)
                agent_username = data_profile['username']
        except TemboardError:
            pass

        return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='alerting.checks.html',
                data={
                    'nav': True,
                    'role': self.role,
                    'instance': self.instance,
                    'plugin': 'alerting',  # we cheat here
                    'agent_username': agent_username
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_index, self.async_callback,
                       (agent_address, agent_port))


class AlertingCheckHTMLHandler(BaseHandler):

    @BaseHandler.catch_errors
    def get_index(self, agent_address, agent_port, check_name):
        self.setUp(agent_address, agent_port)
        xsession = self.get_secure_cookie(
            "temboard_%s_%s" % (agent_address, agent_port))

        if check_name not in check_specs:
            raise TemboardUIError(404, "Unknown check '%s'" % check_name)

        # Here we want to get the current agent username if a session
        # already exists.
        # Monitoring plugin doesn't require agent authentication since we
        # already have the data.
        # Don't fail if there's a session error (for example when the agent
        # has been restarted)
        agent_username = None
        try:
            if xsession:
                data_profile = temboard_profile(self.ssl_ca_cert_file,
                                                agent_address,
                                                agent_port,
                                                xsession)
                agent_username = data_profile['username']
        except TemboardError:
            pass

        # Find host_id & instance_id
        self.host_id = get_host_id(self.db_session, self.instance.hostname)
        self.instance_id = get_instance_id(self.db_session, self.host_id,
                                           self.instance.pg_port)

        query = """
        SELECT *
        FROM monitoring.checks
        WHERE host_id = :host_id
          AND instance_id = :instance_id
          AND name = :check_name
        """
        res = self.db_session.execute(
            query,
            dict(host_id=self.host_id,
                 instance_id=self.instance_id,
                 check_name=check_name))
        check = res.fetchone()
        spec = check_specs[check_name]

        return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='alerting.check.html',
                data={
                    'nav': True,
                    'role': self.role,
                    'instance': self.instance,
                    'check': check,
                    'value_type': spec.get('value_type', None),
                    'plugin': 'alerting',  # we cheat here
                    'agent_username': agent_username
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, check_name):
        run_background(self.get_index, self.async_callback,
                       (agent_address, agent_port, check_name))


class AlertingJSONHandler(JsonHandler):

    def setUp(self, address, port):

        super(AlertingJSONHandler, self).setUp(address, port)

        self.check_active_plugin('monitoring')

        # Find host_id & instance_id
        self.host_id = get_host_id(self.db_session, self.instance.hostname)
        self.instance_id = get_instance_id(self.db_session, self.host_id,
                                           self.instance.pg_port)

    def handle_exception(self, e):
        # Exception handler aimed to return JSONAsyncResult
        self.logger.exception(str(e))
        try:
            self.db_session.close()
        except Exception:
            pass
        # Return 200 with empty list when an error occurs
        no_error = int(self.get_argument('noerror', default=0))
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


class AlertingJSONAlertsHandler(AlertingJSONHandler):

    @BaseHandler.catch_errors
    def get_alerts(self, address, port):
        self.setUp(address, port)

        data_buffer = cStringIO.StringIO()
        cur = self.db_session.connection().connection.cursor()
        cur.execute("SET search_path TO monitoring")
        query = """
        COPY (
            SELECT array_to_json(array_agg(x))
            FROM (
                SELECT json_build_object('description', c.description, 'name', c.name, 'key', sc.key, 'state', sc.state, 'datetime', sc.datetime, 'value', sc.value, 'warning', sc.warning, 'critical', sc.critical) as x
                FROM monitoring.state_changes sc JOIN monitoring.checks c ON (sc.check_id = c.check_id)
                WHERE c.host_id = %s
                  AND c.instance_id = %s
                  AND (sc.state = 'WARNING' OR sc.state = 'CRITICAL')
                ORDER BY sc.datetime desc
                LIMIT 20
            ) as tab
        ) TO STDOUT
        """  # noqa
        # build the query
        query = cur.mogrify(query, (self.host_id, self.instance_id))

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

        return JSONAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def get(self, address, port):
        run_background(self.get_alerts, self.async_callback,
                       (address, port))


class AlertingJSONStateChangesHandler(AlertingJSONHandler):

    @BaseHandler.catch_errors
    def get_state_changes(self, address, port, check_name):
        self.setUp(address, port)

        # Arguments
        start = self.get_argument('start', default=None)
        end = self.get_argument('end', default=None)
        key = self.get_argument('key', default=None)
        if check_name not in check_specs:
            raise TemboardUIError(404, "Unknown check '%s'" % check_name)

        start_time = None
        end_time = None
        if start:
            try:
                start_time = dt_parser.parse(start)
            except ValueError:
                raise TemboardUIError(406, 'Datetime not valid.')
        if end:
            try:
                end_time = dt_parser.parse(end)
            except ValueError:
                raise TemboardUIError(406, 'Datetime not valid.')

        data_buffer = cStringIO.StringIO()
        cur = self.db_session.connection().connection.cursor()
        cur.execute("SET search_path TO monitoring")
        query = """
        COPY (
            SELECT array_to_json(array_agg(json_build_object(
                'datetime', f.datetime,
                'state', f.state,
                'value', f.value,
                'warning', f.warning,
                'critical', f.critical
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
        except Exception:
            # No data
            data = []

        return JSONAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def get(self, address, port, check_name):
        run_background(self.get_state_changes, self.async_callback,
                       (address, port, check_name))


class AlertingJSONChecksHandler(AlertingJSONHandler):

    @BaseHandler.catch_errors
    def get_checks(self, address, port):
        self.setUp(address, port)
        data = checks_info(self.db_session, self.host_id,
                           self.instance_id)
        for datum in data:
            spec = check_specs[datum['name']]
            if 'value_type' in spec:
                datum['value_type'] = spec['value_type']

        return JSONAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def get(self, address, port):
        run_background(self.get_checks, self.async_callback, (address, port))

    @BaseHandler.catch_errors
    def post_checks(self, address, port):
        self.setUp(address, port)

        # POST data reading
        post = tornado.escape.json_decode(self.request.body)
        if 'checks' not in post or type(post.get('checks')) is not list:
            raise TemboardUIError(400, "Post data not valid.")

        for row in post['checks']:
            if row.get('name') not in check_specs:
                raise TemboardUIError(404, "Unknown check '%s'"
                                           % row.get('name'))

        for row in post['checks']:
            # Find the check from its name
            check = self.db_session.query(Check).filter(
                        Check.name == unicode(row.get('name')),
                        Check.host_id == self.host_id,
                        Check.instance_id == self.instance_id).first()
            enabled_before = check.enabled

            if u'enabled' in row:
                enabled_after = bool(row.get(u'enabled'))
                check.enabled = enabled_after
                # detect any change from enabled to disabled
                is_getting_disabled = enabled_before and not enabled_after
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

            if is_getting_disabled:
                cs = self.db_session.query(CheckState).filter(
                    CheckState.check_id == check.check_id,
                )
                for i in cs:
                    i.state = unicode('UNDEF')
                    self.db_session.merge(i)
                    self.db_session.execute(
                        "SELECT monitoring.append_state_changes(:d, :i,"
                        ":s, :k, :v, :w, :c)",
                        {'d': datetime.utcnow(), 'i': check.check_id,
                         's': 'UNDEF', 'k': i.key, 'v': None,
                         'w': check.warning, 'c': check.critical})

        self.db_session.commit()

        return JSONAsyncResult(http_code=200, data=dict())

    @tornado.web.asynchronous
    def post(self, address, port):
        run_background(self.post_checks, self.async_callback, (address, port))


class AlertingJSONCheckChangesHandler(AlertingJSONHandler):

    @BaseHandler.catch_errors
    def get_check_changes(self, address, port, check_name):
        self.setUp(address, port)

        # Arguments
        start = self.get_argument('start', default=None)
        end = self.get_argument('end', default=None)
        if check_name not in check_specs:
            raise TemboardUIError(404, "Unknown check '%s'" % check_name)

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
            SELECT array_to_json(array_agg(json_build_object(
                'datetime', f.datetime,
                'enabled', f.enabled,
                'warning', f.warning,
                'critical', f.critical,
                'description', f.description
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

        return JSONAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def get(self, address, port, check_name):
        run_background(self.get_check_changes, self.async_callback,
                       (address, port, check_name))


class AlertingJSONDetailHandler(AlertingJSONHandler):

    @BaseHandler.catch_errors
    def get_detail(self, address, port, check_name):
        self.setUp(address, port)

        if check_name not in check_specs:
            raise TemboardUIError(404, "Unknown check '%s'" % check_name)

        detail = check_state_detail(self.db_session, self.host_id,
                                    self.instance_id, check_name)
        for d in detail:
            spec = check_specs[check_name]
            if 'value_type' in spec:
                d['value_type'] = spec['value_type']
        return JSONAsyncResult(http_code=200, data=detail)

    @tornado.web.asynchronous
    def get(self, address, port, check_name):
        run_background(self.get_detail, self.async_callback,
                       (address, port, check_name))
