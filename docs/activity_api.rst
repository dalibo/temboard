.. _activity_api:

Activity plugin API
===================

.. http:get:: /activity

    Get list of PostgreSQL backends.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /activity HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
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
            }
        ]
    }


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 401 Unauthorized
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:58:00 GMT
    Content-type: application/json

    {"error": "Invalid session."}


.. sourcecode:: http

    HTTP/1.0 406 Not Acceptable
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:58:00 GMT
    Content-type: application/json

    {"error": "Parameter 'X-Session' is malformed."}


.. http:get:: /activity/waiting

    Get list of PostgreSQL backends waiting for lock acquisition.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /activity/waiting HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
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
            }
        ]
    }


.. http:get:: /activity/blocking

    Get list of PostgreSQL backends blocking other backends due to lock acquisition.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /activity/blocking HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
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
            }
        ]
    }


.. http:post:: /activity/activity/kill

    Terminate (kill) a list of PostgreSQL backends.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    POST /activity/kill HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-Type: application/json

    {
        "pids":
        [
            13309
        ]
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "backends":
        [
            {"pid": 13309, "killed": true},
        ]
    }
