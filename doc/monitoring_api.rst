.. _monitoring_api:

Monitoring plugin API
=====================

.. http:get:: /monitoring/probe/sessions

    Run ``sessions`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/sessions HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "sessions":
        [
            {
                "idle_in_xact": 0,
                "idle_in_xact_aborted": 0,
                "no_priv": 0,
                "idle": 0,
                "datetime": "2017-04-21 08:24:45.003511+02",
                "disabled": 0,
                "waiting": 0,
                "port": 5432,
                "active": 0,
                "dbname": "temboard_test",
                "fastpath": 0
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


.. http:get:: /monitoring/probe/xacts

    Run ``xacts`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/xacts HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "xacts":
        [
            {
                "port": 5432,
                "n_commit": 0,
                "n_rollback": 0,
                "dbname": "template1",
                "datetime": "2017-04-21 08:42:12.092111+02"
            }
        ]
    }


.. http:get:: /monitoring/probe/locks

    Run ``locks`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.

**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/locks HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "locks":
        [
            {
                "exclusive": 0,
                "waiting_share_row_exclusive": 0,
                "waiting_share": 0,
                "row_share": 0,
                "waiting_row_exclusive": 0,
                "share_row_exclusive": 0,
                "port": 5432,
                "share": 0,
                "waiting_access_share": 0,
                "dbname": "test",
                "row_exclusive": 0,
                "share_update_exclusive": 0,
                "access_share": 0,
                "access_exclusive": 0,
                "waiting_exclusive": 0,
                "siread": 0,
                "datetime": "2017-04-21 08:55:11.768602+02",
                "waiting_share_update_exclusive": 0,
                "waiting_row_share": 0,
                "waiting_access_exclusive": 0
            }
        ]
    }


.. http:get:: /monitoring/probe/blocks

    Run ``blocks`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/blocks HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "blocks":
        [
            {
                "blks_read": 382,
                "dbname": "postgres",
                "hitmiss_ratio": 99.9998294969873,
                "blks_hit": 224042580,
                "datetime": "2017-04-21 08:57:32.11277+02",
                "port": 5432
            }
        ]
    }


.. http:get:: /monitoring/probe/bgwriter

    Run ``bgwriter`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/bgwriter HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "bgwriter":
        [
            {
                "checkpoint_write_time": 15113301.0,
                "checkpoints_timed": 1960,
                "buffers_alloc": 29369,
                "buffers_clean": 0,
                "buffers_backend_fsync": 0,
                "checkpoint_sync_time": 177464.0,
                "checkpoints_req": 0,
                "port": 5432,
                "buffers_backend": 42258,
                "maxwritten_clean": 0,
                "datetime": "2017-04-21 08:59:20.171443+02",
                "buffers_checkpoint": 149393,
                "stats_reset": "2017-04-14 13:37:15.288701+02"
            }
        ]
    }


.. http:get:: /monitoring/probe/db_size

    Run ``db_size`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/db_size HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "db_size":
        [
            {
                "port": 5432,
                "size": 7021060,
                "dbname": "template1",
                "datetime": "2017-04-21 09:00:47.528365+02"
            },
            {
                "port": 5432,
                "size": 7168172,
                "dbname": "postgres",
                "datetime": "2017-04-21 09:00:47.528365+02"
            }
        ]
    }


.. http:get:: /monitoring/probe/tblspc_size

    Run ``tblspc_size`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/tblspc_size HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "tblspc_size":
        [
            {
                "size": 181067120,
                "port": 5432,
                "spcname": "pg_default",
                "datetime": "2017-04-21 09:13:55.196718+02"
            },
            {
                "size": 622400,
                "port": 5432,
                "spcname": "pg_global",
                "datetime": "2017-04-21 09:13:55.196718+02"
            },
            {
                "size": null,
                "port": 5432,
                "spcname": "tbs",
                "datetime": "2017-04-21 09:13:55.196718+02"
            }
        ]
    }


.. http:get:: /monitoring/probe/filesystems_size

    Run ``filesystems_size`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/filesystems_size HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "filesystems_size":
        [
            {
                "device": "udev",
                "total": 10485760,
                "mount_point": "/dev",
                "used": 4096,
                "datetime": "2017-04-21 07:16:25 +0000"
            },
            {
                "device": "/dev/sda4",
                "total": 21003628544,
                "mount_point": "/",
                "used": 11889070080,
                "datetime": "2017-04-21 07:16:25 +0000"
            }
        ]
    }


.. http:get:: /monitoring/probe/cpu

    Run ``cpu`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/cpu HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "cpu":
        [
            {
                "time_system": 140,
                "time_steal": 0,
                "time_iowait": 10,
                "datetime": "2017-04-21 08:09:27 +0000",
                "measure_interval": 27.88518500328064,
                "time_idle": 27410,
                "cpu": "cpu0",
                "time_user": 290
            },
            {
                "time_system": 110,
                "time_steal": 0,
                "time_iowait": 10,
                "datetime": "2017-04-21 08:09:27 +0000",
                "measure_interval": 27.885642051696777,
                "time_idle": 27410,
                "cpu": "cpu1",
                "time_user": 290
            },
            {
                "time_system": 170,
                "time_steal": 0,
                "time_iowait": 1390,
                "datetime": "2017-04-21 08:09:27 +0000",
                "measure_interval": 27.885895013809204,
                "time_idle": 26040,
                "cpu": "cpu2",
                "time_user": 220
            },
            {
                "time_system": 130,
                "time_steal": 0,
                "time_iowait": 20,
                "datetime": "2017-04-21 08:09:27 +0000",
                "measure_interval": 27.88606309890747,
                "time_idle": 27370,
                "cpu": "cpu3",
                "time_user": 320
            }
        ]
    }


.. http:get:: /monitoring/probe/process

    Run ``process`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/process HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "process":
        [
            {
                "measure_interval": 55.731096029281616,
                "procs_total": "486",
                "forks": 165,
                "procs_blocked": 0,
                "context_switches": 31453,
                "procs_running": 4,
                "datetime": "2017-04-21 08:13:56 +0000"
            }
        ]
    }


.. http:get:: /monitoring/probe/memory

    Run ``memory`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/memory HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "memory":
        [
            {
                "mem_used": 7268151296,
                "swap_used": 0,
                "swap_total": 4026527744,
                "mem_total": 8276094976,
                "mem_cached": 2464796672,
                "mem_free": 1007943680,
                "mem_buffers": 558067712,
                "datetime": "2017-04-21 08:15:06 +0000"
            }
        ]
    }


.. http:get:: /monitoring/probe/loadavg

    Run ``loadavg`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/loadavg HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "loadavg":
        [
            {
                "load1": "0.07",
                "load15": "0.09",
                "load5": "0.16",
                "datetime": "2017-04-21 08:16:16 +0000"
            }
        ]
    }


.. http:get:: /monitoring/probe/wal_files

    Run ``wal_files`` monitoring probe.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /monitoring/probe/wal_files HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.12
    Date: Fri, 21 Apr 2017 06:24:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "wal_files":
        [
            {
                "archive_ready": 0,
                "total_size": 201326592.0,
                "written_size": 13648,
                "datetime": "2017-04-21 08:17:12 +0000",
                "measure_interval": 9.273101091384888,
                "current_location": "53/700035B0",
                "total": 12,
                "port": 5432
            }
        ]
    }
