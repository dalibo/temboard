"""
The inventory contains support functions to discover the features of the host
(ex: OS, CPU info, MemInfo)

Currently, only Linux is supported.
"""

import os
import logging
import pwd

from ...inventory import (
    SysInfo,
    PgInfo,
)


def host_info(discover):
    """Gather system information."""
    sinfo = SysInfo()

    s = discover['system']
    hostinfo = {
        "os": s['os'],
        "os_version": s['os_version'],
        "cpu_arch": s['arch'],
        "hostname": s['fqdn'],
    }
    hostinfo.update(sinfo.cpu_info())
    hostinfo['memory_size'] = s['memory']
    hostinfo['ip_addresses'] = sinfo.ip_addresses()
    hostinfo['filesystems'] = sinfo.file_systems()
    hostinfo['os_flavor'] = s['distribution']
    return hostinfo


def instance_info(pool, conninfo, discover):
    """Gather PostgreSQL instance information."""
    instance_info = {
        'hostname': discover['system']['fqdn'],
        'instance': conninfo['instance'],
        'local_name': conninfo.get('local_name', conninfo['instance']),
        'available': True,
        'host': conninfo['host'],
        'port': conninfo['port'],
        'user': conninfo['user'],
        'database': conninfo['database'],
        'password': conninfo['password']
    }
    p = discover['postgres']

    # Try the connection
    try:
        conn = pool.getconn(dbname=conninfo['database'])
        # Get PostgreSQL informations using PgInfo
        pginfo = PgInfo(conn)
        # Gather the info while where are connected
        instance_info['version_num'] = p['version_num']
        instance_info['version'] = p['version']
        instance_info['data_directory'] = p['data_directory']
        instance_info['max_connections'] = p['max_connections']
        instance_info['start_time'] = pginfo.start_time()

        # hot standby is available from 9.0
        instance_info['standby'] = pginfo.is_in_recovery()

        # Grab the list of tablespaces
        instance_info['tablespaces'] = pginfo.tablespaces(
            instance_info['data_directory'])

        # When the user has not given a dbnames list or '*' in the
        # configuration file, we must get the list of databases. Since
        # we have a working connection, let's do it now.
        dbs = pginfo.databases()
        instance_info['dbnames'] = []
        for db in conninfo['dbnames']:
            if db == '*':
                instance_info['dbnames'] = list(dbs.values())
                break
            if db in dbs.keys():
                instance_info['dbnames'].append(dbs[db])

        # Now that we have the data_directory, find the owner
        try:
            statinfo = os.stat(instance_info['data_directory'])
            instance_info['sysuser'] = pwd.getpwuid(statinfo.st_uid).pw_name
        except OSError as e:
            logging.warning("Unable to get the owner of PGDATA: %s", str(e))
            instance_info['sysuser'] = None

    except Exception as e:
        logging.exception(str(e))
        logging.warning("Unable to gather information for cluster \"%s\"",
                        conninfo['instance'])
        instance_info['available'] = False

    return instance_info
