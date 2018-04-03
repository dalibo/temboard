.. _dashboard_api:

Dashboard plugin API
====================

.. http:get:: /dashboard

    Get the whole last data set used to render dashboard view. Data have been collected async.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Content-type: application/json

    {
        "active_backends":
        {
            "nb": 1,
            "time": 1429617751.29224
        },
        "loadaverage": 0.28,
        "os_version": "Linux 3.16.0-34-generic x86_64",
        "pg_version": "9.4.1",
        "n_cpu": "4",
        "hitratio": 98.0,
        "databases":
        {
            "total_size": "1242 MB",
            "time": "14:02",
            "databases": 4,
            "total_commit": 16728291,
            "total_rollback": 873
        },
        "memory": {
            "total": 3950660,
            "active": 46.9,
            "cached": 20.2,
            "free": 32.9
        },
        "hostname": "neptune",
        "cpu":
        {
            "iowait": 0.0,
            "idle": 97.5,
            "steal": 0.0,
            "user": 2.5,
            "system": 0.0
        },
        "buffers":
        {
            "nb": 348247,
            "time": 1429617751.276508
        }
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


.. http:get:: /dashboard/config

    Get the dashboard plugin config.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Content-type: application/json

    {
        "history_length": 150,
        "scheduler_interval": 2
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


.. http:get:: /dashboard/live

    Synchronous version of ``/dashboard``. Please refer to ``/dashboard`` API documentation for details.


.. http:get:: /dashboard/history

    Get the last ``n`` sets of dashboard data. ``n`` is defined by parameter ``history_length`` from the ``dashboard`` section of configuration file. Default value is ``150``.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/history HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 15:56:56 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "active_backends":
            {
                "nb": 1,
                "time": 1492703660.798522
            },
            "max_connections": 100,
            "databases":
            {
                "total_rollback": 1081,
                "total_size": "158 MB",
                "timestamp": 1492703660.913077,
                "time": "17:54",
                "total_commit": 2825374,
                "databases": 6
            },
            "hostname": "poseidon.home.priv",
            "pg_version": "PostgreSQL 9.5.5 on x86_64-pc-linux-gnu, compiled by x86_64-pc-linux-gnu-gcc (Gentoo 4.9.4 p1.0, pie-0.6.4) 4.9.4, 64-bit",
            "memory":
            {
                "active": 51.0,
                "cached": 29.5,
                "total": 8082124,
                "free": 19.5
            },
            "cpu":
            {
                "iowait": 0.0,
                "idle": 100.0,
                "steal": 0.0,
                "user": 0.0,
                "system": 0.0
            },
            "os_version": "Linux 4.9.6-gentoo-r1",
            "loadaverage": 0.18,
            "hitratio": 99.0,
            "pg_uptime": "01:50:31.573788",
            "pg_port": "5432",
            "n_cpu": 4,
            "pg_data": "/var/lib/postgresql/9.5/data",
            "buffers":
            {
                "nb": 27670,
                "time": 1492703660.784254
            }
        }
    ]


.. http:get:: /dashboard/buffers

    Get the number of buffers allocated by PostgreSQL ``background writer`` process.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/buffers HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:09:58 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"buffers": {"nb": 27696, "time": 1492704598.784161}}


.. http:get:: /dashboard/hitratio

    Get PostgreSQL global cache hit ratio.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/hitratio HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:28:33 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"hitratio": 99.0}


.. http:get:: /dashboard/active_backends

    Get the total number of active backends.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/active_backends HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:35:55 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "active_backends":
        {
            "nb": 1,
            "time": 1492706155.986045
        }
    }


.. http:get:: /dashboard/cpu

    Get CPU usage.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/cpu HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:40:46 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "cpu":
        {
            "iowait": 0.0,
            "idle": 100.0,
            "steal": 0.0,
            "user": 0.0,
            "system": 0.0
        }
    }


.. http:get:: /dashboard/loadaverage

    System loadaverage.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/loadaverage HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:44:04 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "loadaverage": 0.06
    }


.. http:get:: /dashboard/memory

    Memory usage.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/memory HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:46:39 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "memory":
        {
            "active": 50.1,
            "cached": 29.5,
            "total": 8082124,
            "free": 20.4
        }
    }


.. http:get:: /dashboard/hostname

    Machine hostname.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/hostname HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:48:49 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "hostname": "poseidon.home.priv"
    }


.. http:get:: /dashboard/os_version

    Operating system version.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/os_version HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:55:44 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "os_version": "Linux 4.9.6-gentoo-r1"
    }


.. http:get:: /dashboard/pg_version

    Get PostgreSQL server version.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/pg_version HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:59:26 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "pg_version": "PostgreSQL 9.5.5 on x86_64-pc-linux-gnu, compiled by x86_64-pc-linux-gnu-gcc (Gentoo 4.9.4 p1.0, pie-0.6.4) 4.9.4, 64-bit"
    }


.. http:get:: /dashboard/n_cpu

    Number of CPU.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/n_cpu HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 17:03:55 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "n_cpu": 4
    }


.. http:get:: /dashboard/databases

    PostgreSQL cluster size & number of databases.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/databases HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 17:08:59 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "databases":
        {
            "total_rollback": 1087,
            "total_size": "159 MB",
            "timestamp": 1492708139.981268,
            "databases": 6,
            "total_commit": 2848707,
            "time": "19:08"
        }
    }


.. http:get:: /dashboard/info

    Get a bunch of global informations about system and PostgreSQL.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/info HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 17:17:57 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "hostname": "poseidon.home.priv",
        "os_version": "Linux 4.9.6-gentoo-r1",
        "pg_port": "5432",
        "pg_uptime": "03:14:08.029574",
        "pg_version": "PostgreSQL 9.5.5 on x86_64-pc-linux-gnu, compiled by x86_64-pc-linux-gnu-gcc (Gentoo 4.9.4 p1.0, pie-0.6.4) 4.9.4, 64-bit",
        "pg_data": "/var/lib/postgresql/9.5/data"
    }


.. http:get:: /dashboard/max_connections

    Get the max_connections settings value.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


.. sourcecode:: http

    GET /dashboard/active_backends HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Thu, 20 Apr 2017 16:35:55 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "max_connections": 100
    }
