import time
import os
import sys
import re
import logging
import signal
import json
import urllib2

try:
    from configparser import NoOptionError
except ImportError:
    from ConfigParser import NoOptionError


from temboardagent.routing import add_route, add_worker
from temboardagent.configuration import (
    PluginConfiguration,
    ConfigurationError,
)
from temboardagent.logger import get_logger, set_logger_name, get_tb
from temboardagent.sharedmemory import Command
from temboardagent.tools import hash_id
from temboardagent.errors import (
    HTTPError,
    SharedItem_exists,
    SharedItem_no_free_slot_left,
)
from temboardagent.workers import (
    COMMAND_START,
)
from temboardagent.api import check_sessionid
from temboardagent.queue import Queue, Message
from temboardagent.tools import now
from temboardagent.inventory import SysInfo

from monitoring.inventory import host_info, instance_info
from monitoring.probes import (
    load_probes,
    probe_bgwriter,
    probe_blocks,
    probe_cpu,
    probe_db_size,
    probe_filesystems_size,
    probe_loadavg,
    probe_locks,
    probe_memory,
    probe_process,
    probe_replication,
    probe_sessions,
    probe_tblspc_size,
    probe_wal_files,
    probe_xacts,
    run_probes,
)
from monitoring.output import send_output, remove_passwords

__VERSION__ = '0.0.1'


@add_route('GET', '/monitoring/probe/sessions')
def monitoring_probe_sessions(http_context, queue_in=None, config=None,
                              sessions=None, commands=None):
    """
Run ``sessions`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/sessions HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.

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


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_sessions(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/xacts')
def monitoring_probe_xacts(http_context, queue_in=None, config=None,
                           sessions=None, commands=None):
    """
Run ``xacts`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/xacts HTTP/1.1
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


:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_xacts(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/locks')
def monitoring_probe_locks(http_context, queue_in=None, config=None,
                           sessions=None, commands=None):
    """
Run ``locks`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/locks HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_locks(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/blocks')
def monitoring_probe_blocks(http_context, queue_in=None, config=None,
                            sessions=None, commands=None):
    """
Run ``blocks`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/blocks HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_blocks(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/bgwriter')
def monitoring_probe_bgwriter(http_context, queue_in=None, config=None,
                              sessions=None, commands=None):
    """
Run ``bgwriter`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/bgwriter HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_bgwriter(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/db_size')
def monitoring_probe_db_size(http_context, queue_in=None, config=None,
                             sessions=None, commands=None):
    """
Run ``db_size`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/db_size HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_db_size(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/tblspc_size')
def monitoring_probe_tblspc_size(http_context, queue_in=None, config=None,
                                 sessions=None, commands=None):
    """
Run ``tblspc_size`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/tblspc_size HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_tblspc_size(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/filesystems_size')
def monitoring_probe_filesystems_size(http_context, queue_in=None, config=None,
                                      sessions=None, commands=None):
    """
Run ``filesystems_size`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/filesystems_size HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(
            probe_filesystems_size(config.plugins['monitoring']),
            config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/cpu')
def monitoring_probe_cpu(http_context, queue_in=None, config=None,
                         sessions=None, commands=None):
    """
Run ``cpu`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/cpu HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_cpu(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/process')
def monitoring_probe_process(http_context, queue_in=None, config=None,
                             sessions=None, commands=None):
    """
Run ``process`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/process HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_process(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/memory')
def monitoring_probe_memory(http_context, queue_in=None, config=None,
                            sessions=None, commands=None):
    """
Run ``memory`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/memory HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_memory(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/loadavg')
def monitoring_probe_loadavg(http_context, queue_in=None, config=None,
                             sessions=None, commands=None):
    """
Run ``loadavg`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/loadavg HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_loadavg(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/wal_files')
def monitoring_probe_wal_files(http_context, queue_in=None, config=None,
                               sessions=None, commands=None):
    """
Run ``wal_files`` monitoring probe.

**Example request**:

.. sourcecode:: http

    GET /monotoring/probe/wal_files HTTP/1.1
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

:reqheader X-Session: Session ID
:statuscode 200: no error
:statuscode 401: invalid session
:statuscode 500: internal error
:statuscode 406: header ``X-Session`` is malformed.


    """  # noqa
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_wal_files(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


@add_route('GET', '/monitoring/probe/replication')
def monitoring_probe_replication(http_context, queue_in=None, config=None,
                                 sessions=None, commands=None):
    set_logger_name("monitoring")
    logger = get_logger(config)
    check_sessionid(http_context['headers'], sessions)

    try:
        output = api_run_probe(probe_replication(config.plugins['monitoring']),
                               config)
        return output
    except Exception as e:
        logger.error(str(e.message))
        raise HTTPError(500, "Internal error.")


def api_run_probe(probe_instance, config):
    """
    Run a probe instance.
    """
    set_logger_name("monitoring")
    logger = get_logger(config)
    # TODO: logging methods in monitoring_agent code and monitoring_agent
    # should be aligned.
    logging.root = logger
    config.plugins['monitoring']['conninfo'] = [{
        'host': config.postgresql['host'],
        'port': config.postgresql['port'],
        'user': config.postgresql['user'],
        'database': config.postgresql['dbname'],
        'password': config.postgresql['password'],
        'dbnames': config.plugins['monitoring']['dbnames'],
        'instance': config.postgresql['instance']
    }]
    # Validate connection information from the config, and ensure
    # the instance is available
    instances = []
    sysinfo = SysInfo()
    hostname = sysinfo.hostname(config.temboard['hostname'])
    for conninfo in config.plugins['monitoring']['conninfo']:
        logging.debug("Validate connection information on instance \"%s\"",
                      conninfo['instance'])
        instances.append(instance_info(conninfo, hostname))

    # Set home path
    probe_instance.set_home(config.temboard['home'])
    # Gather the data from probes
    data = run_probes([probe_instance], instances, delta=False)
    return data


@add_worker(b'monitoring_collector')
def monitoring_collector_worker(commands, command, config):
    """
    Run probes and push collected metrics in a queue.
    """
    signal.signal(signal.SIGTERM, monitoring_worker_sigterm_handler)

    start_time = time.time() * 1000
    set_logger_name("monitoring_collector_worker")
    logger = get_logger(config)
    # TODO: logging methods in monitoring plugin must be aligned.
    logging.root = logger
    logger.debug("Starting with pid=%s" % (os.getpid()))
    logger.debug("commandid=%s" % (command.commandid))
    command.state = COMMAND_START
    command.time = time.time()

    try:
        command.pid = os.getpid()
        commands.update(command)
        system_info = host_info(config.temboard['hostname'])
    except (ValueError, Exception) as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        sys.exit(1)

    # Load the probes to run
    try:
        probes = load_probes(config.plugins['monitoring'],
                             config.temboard['home'])
        config.plugins['monitoring']['conninfo'] = [{
            'host': config.postgresql['host'],
            'port': config.postgresql['port'],
            'user': config.postgresql['user'],
            'database': config.postgresql['dbname'],
            'password': config.postgresql['password'],
            'dbnames': config.plugins['monitoring']['dbnames'],
            'instance': config.postgresql['instance']
        }]

        # Validate connection information from the config, and ensure
        # the instance is available
        instances = []
        for conninfo in config.plugins['monitoring']['conninfo']:
            logging.debug("Validate connection information on instance \"%s\"",
                          conninfo['instance'])
            instances.append(instance_info(conninfo, system_info['hostname']))

        # Gather the data from probes
        data = run_probes(probes, instances)

        # Prepare and send output
        output = {
            'datetime': now(),
            'hostinfo': system_info,
            'instances': remove_passwords(instances),
            'data': data,
            'version': __VERSION__
        }
        logger.debug("Collected data: %s" % (output))
        q = Queue('%s/metrics.q' % (config.temboard['home']),
                  max_size=1024 * 1024 * 10, overflow_mode='slide')
        q.push(Message(content=json.dumps(output)))
    except Exception as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        sys.exit(1)

    logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
    logger.debug("Done.")


@add_worker(b'monitoring_sender')
def monitoring_sender_worker(commands, command, config):
    signal.signal(signal.SIGTERM, monitoring_worker_sigterm_handler)
    start_time = time.time() * 1000
    set_logger_name("monitoring_sender_worker")
    logger = get_logger(config)
    # TODO: logging methods in monitoring plugin must be aligned.
    logging.root = logger
    logger.debug("Starting with pid=%s" % (os.getpid()))
    logger.debug("commandid=%s" % (command.commandid))
    command.state = COMMAND_START
    command.time = time.time()
    command.pid = os.getpid()
    commands.update(command)
    c = 0
    while True:
        # Let's do it smoothly..
        time.sleep(0.5)

        q = Queue('%s/metrics.q' % (config.temboard['home']),
                  max_size=1024 * 1024 * 10, overflow_mode='slide')
        msg = q.shift(delete=False)
        if msg is None:
            break
        try:
            send_output(config.plugins['monitoring']['ssl_ca_cert_file'],
                        config.plugins['monitoring']['collector_url'],
                        config.temboard['key'],
                        msg.content)
        except urllib2.HTTPError as e:
            logger.traceback(get_tb())
            logger.error(str(e))
            # On an error 409 (DB Integrity) we need to remove the message.
            if int(e.code) != 409:
                logger.debug(
                    "Duration: %s." % (str(time.time() * 1000 - start_time)))
                logger.debug("Failed.")
                sys.exit(1)
        except Exception as e:
            logger.traceback(get_tb())
            logger.error(str(e))
            logger.debug(
                "Duration: %s." % (str(time.time() * 1000 - start_time)))
            logger.debug("Failed.")
            sys.exit(1)

        # If everything's fine then remove current msg from the queue
        q.shift(delete=True, check_msg=msg)

        if c > 60:
            break
        c += 1
    logger.debug("Duration: %s." % (str(time.time() * 1000 - start_time)))
    logger.debug("Done.")


def scheduler(queue_in, config, commands):
    # Schedule collector worker.
    schedule_worker(queue_in, config, commands, b'monitoring_collector')
    # Schedule sender worker.
    schedule_worker(queue_in, config, commands, b'monitoring_sender')


def schedule_worker(queue_in, config, commands, worker, parameters=''):
    # Check command uniqueness.
    try:
        commands.check_uniqueness(worker, parameters)
    except SharedItem_exists:
        return

    cid = hash_id(worker)
    command = Command(cid.encode('utf-8'), time.time(), 0, worker, parameters,
                      0, u'')
    try:
        commands.add(command)
        # Put the Command in the command queue
        queue_in.put(command)
        return
    except SharedItem_no_free_slot_left:
        return


def configuration(config):
    class Configuration(PluginConfiguration):
        def __init__(self, config, *args, **kwargs):
            PluginConfiguration.__init__(self, config.configfile, *args,
                                         **kwargs)

            self.plugin_configuration = {
                'dbnames': '*',
                'scheduler_interval': 60,
                'probes': '*',
                'collector_url': None,
                'ssl_ca_cert_file': None
            }
            set_logger_name("monitoring")
            logger = get_logger(config)

            try:
                self.check_section(__name__)
            except ConfigurationError:
                return

            try:
                dbnames = self.get(__name__, 'dbnames')
                self.plugin_configuration['dbnames'] = re.split(r'[,\s]+',
                                                                dbnames)
            except NoOptionError:
                pass

            try:
                probes = self.get(__name__, 'probes')
                self.plugin_configuration['probes'] = re.split(r'[,\s]+',
                                                               probes)
            except NoOptionError:
                pass

            try:
                collector_url = self.get(__name__, 'collector_url')
                self.plugin_configuration['collector_url'] = collector_url
            except NoOptionError:
                pass

            try:
                if not (self.getint(__name__, 'scheduler_interval') > 0 and
                        self.getint(__name__, 'scheduler_interval') < 86400):
                    raise ValueError()
                self.plugin_configuration['scheduler_interval'] = \
                    self.getint(__name__, 'scheduler_interval')
            except ValueError:
                logger.error("%s - configuration error: 'scheduler_interval' "
                             "must be an integer between 0 and 86400 in '%s' "
                             "section in %s."
                             % (__name__, self.configfile, __name__))
            except NoOptionError:
                pass

            try:
                with open(self.get(__name__, 'ssl_ca_cert_file')) as fd:
                    fd.read()
                    self.plugin_configuration['ssl_ca_cert_file'] = \
                        self.get(__name__, 'ssl_ca_cert_file')
            except Exception:
                raise ConfigurationError(
                    "SSL CA certificates file %s can't be opened."
                    % (self.get(__name__, 'ssl_ca_cert_file')))
            except NoOptionError:
                pass

    c = Configuration(config)
    return c.plugin_configuration


def monitoring_worker_sigterm_handler(signum, frame):
    logging.info("monitoring_worker - SIGTERM")
    sys.exit(1)
