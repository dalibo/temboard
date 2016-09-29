from temboardagent.routing import add_route, add_worker
from temboardagent.api_wrapper import *
from temboardagent.logger import set_logger_name
import activity.functions as activity_functions

@add_route('GET', '/activity')
def get_activity(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /activity Get the list of backend.
    @apiVersion 0.0.1
    @apiName Activity
    @apiGroup Activity

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object[]} response.rows List of backends.
    @apiSuccess {Number}   response.rows.pid Process ID of this backend.
    @apiSuccess {String}   response.rows.database Name of the database this backend is connected to.
    @apiSuccess {String}   response.rows.user Name of the user logged into this backend.
    @apiSuccess {String}   response.rows.client IP address of the client connected to this backend.
    @apiSuccess {Number}   response.rows.cpu CPU usage (%) of this backend.
    @apiSuccess {Number}   response.rows.memory Memory usage (%) of this backend.
    @apiSuccess {String}   response.rows.read_s Read rate of this backend.
    @apiSuccess {String}   response.rows.write_s Write rate of this backend.
    @apiSuccess {String}   response.rows.iow Is this backend waiting for IO operations.
    @apiSuccess {String}   response.rows.w Is this backend waiting for lock acquisition.
    @apiSuccess {Number}   response.rows.duration Query duration (s).
    @apiSuccess {String}   response.rows.state State of this backend.
    @apiSuccess {String}   response.rows.query Query.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/activity

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "rows":
            [
                {
                    "pid": 6285,
                    "database": "postgres",
                    "user": "postgres",
                    "client": null,
                    "cpu": 0.0,
                    "memory": 0.13,
                    "read_s": "0.00B",
                    "write_s": "0.00B",
                    "iow": "N",
                    "wait": "N",
                    "duration": "1.900",
                    "state": "idle",
                    "query": "SELECT 1;"
                },
                ...
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """
    set_logger_name('activity')
    return api_function_wrapper_pg(config, http_context, sessions, activity_functions, 'get_activity')

@add_route('GET', '/activity/waiting')
def get_activity_waiting(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /activity/waiting Get the list of backend waiting for lock acquisition.
    @apiVersion 0.0.1
    @apiName ActivityWaiting
    @apiGroup Activity

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object[]} response.rows List of backends.
    @apiSuccess {Number}   response.rows.pid Process ID of this backend.
    @apiSuccess {String}   response.rows.database Name of the database this backend is connected to.
    @apiSuccess {String}   response.rows.user Name of the user logged into this backend.
    @apiSuccess {Number}   response.rows.cpu CPU usage (%) of this backend.
    @apiSuccess {Number}   response.rows.memory Memory usage (%) of this backend.
    @apiSuccess {String}   response.rows.read_s Read rate of this backend.
    @apiSuccess {String}   response.rows.write_s Write rate of this backend.
    @apiSuccess {String}   response.rows.iow Is this backend waiting for IO operations.
    @apiSuccess {Number}   response.rows.relation OID of the relation targeted by the lock.
    @apiSuccess {Number}   response.rows.type Type of lockable object.
    @apiSuccess {Number}   response.rows.mode Name of the lock mode held or desired by this process.
    @apiSuccess {Number}   response.rows.duration Query duration (s).
    @apiSuccess {String}   response.rows.state State of this backend.
    @apiSuccess {String}   response.rows.query Query.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/activity/waiting

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "rows":
            [
                {
                    "pid": 13532,
                    "database": "test",
                    "user": "postgres",
                    "cpu": 0.0,
                    "memory": 0.16,
                    "read_s": "0.00B",
                    "write_s": "0.00B",
                    "iow": "N",
                    "relation": " ",
                    "type": "transactionid",
                    "mode": "ShareLock",
                    "state": "active",
                    "duration": 4.35,
                    "query": "DELETE FROM t1 WHERE id = 1;"
                },
                ...
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """
    set_logger_name('activity')
    return api_function_wrapper_pg(config, http_context, sessions, activity_functions, 'get_activity_waiting')

@add_route('GET', '/activity/blocking')
def get_activity_blocking(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /activity/blocking Get the list of backend blocking other backends due to lock acquisition.
    @apiVersion 0.0.1
    @apiName ActivityBlocking
    @apiGroup Activity

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object[]} response.rows List of backends.
    @apiSuccess {Number}   response.rows.pid Process ID of this backend.
    @apiSuccess {String}   response.rows.database Name of the database this backend is connected to.
    @apiSuccess {String}   response.rows.user Name of the user logged into this backend.
    @apiSuccess {Number}   response.rows.cpu CPU usage (%) of this backend.
    @apiSuccess {Number}   response.rows.memory Memory usage (%) of this backend.
    @apiSuccess {String}   response.rows.read_s Read rate of this backend.
    @apiSuccess {String}   response.rows.write_s Write rate of this backend.
    @apiSuccess {String}   response.rows.iow Is this backend waiting for IO operations.
    @apiSuccess {Number}   response.rows.relation OID of the relation targeted by the lock.
    @apiSuccess {Number}   response.rows.type Type of lockable object.
    @apiSuccess {Number}   response.rows.mode Name of the lock mode held or desired by this process.
    @apiSuccess {String}   response.rows.state State of this backend.
    @apiSuccess {Number}   response.rows.duration Query duration (s).
    @apiSuccess {String}   response.rows.query Query.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/activity/blocking

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "rows":
            [
                {
                    "pid": 13309,
                    "database": "test",
                    "user": "postgres",
                    "cpu": 0.0,
                    "memory": 0.2,
                    "read_s": "0.00B",
                    "write_s": "0.00B",
                    "iow": "N",
                    "relation": " ",
                    "type": "transactionid",
                    "mode": "ExclusiveLock",
                    "state": "idle in transaction",
                    "duration": 4126.98,
                    "query": "UPDATE t1 SET id = 100000000 where id =1;"
                },
                ...
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """
    set_logger_name('activity')
    return api_function_wrapper_pg(config, http_context, sessions, activity_functions, 'get_activity_blocking')

@add_route('POST', '/activity/kill')
def post_activity_kill(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {post} /activity/kill Terminate N backends.
    @apiVersion 0.0.1
    @apiName ActivityKill
    @apiGroup Activity

    @apiHeader {String} X-Session Session ID.
    @apiParam  {String[]} pids List of process ID to terminate.

    @apiSuccess {Object[]} response.backends List of backend status.
    @apiSuccess {Number}   response.backends.pid Process ID of this backend.
    @apiSuccess {Boolean}  response.backends.killes Was the backend killed ?

    @apiExample {curl} Example usage:
        curl -k -X POST -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
            -H "Content-Type: application/json" --data '{"pids": [ 13309 ]}' \
            "https://localhost:2345/activity/kill"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "backends":
            [
                {"pid": 13309, "killed": true},
                ...
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """
    set_logger_name('activity')
    return api_function_wrapper_pg(config, http_context, sessions, activity_functions, 'post_activity_kill')
