from copy import deepcopy
import json


# As returned by db.get_metrics(). Copy-pasted payload from dev env.
temboard_data = json.loads("""\
{
  "datetime": "2022-07-08 10:38:58 +0000",
  "hostinfo": {
    "hostname": "postgres0.dev",
    "os": "Linux",
    "os_version": "5.10.0-15-amd64",
    "cpu_arch": "x86_64",
    "cpus": [
    ],
    "cpu_count": 8,
    "memory_size": 16417996800,
    "ip_addresses": [
    "127.0.0.1",
    "172.19.0.13"
    ],
    "filesystems": [],
    "os_flavor": "Debian 11.2"
  },
  "instances": [
    {
      "hostname": "postgres0.dev",
      "instance": "main",
      "local_name": "main",
      "available": true,
      "host": "/run/postgresql",
      "port": 5432,
      "user": "postgres",
      "database": "postgres",
      "version_num": 140003,
      "version": "14.3",
      "data_directory": "/var/lib/postgresql/data",
      "standby": false,
      "max_connections": "100",
      "tablespaces": null,
      "dbnames": [
      ],
      "start_time": "2022-07-08T10:18:58.000000+0000",
      "sysuser": "postgres"
    }
  ],
  "data": {
    "sessions": [
      {
        "dbname": "postgres",
        "active": 1,
        "waiting": 0,
        "idle": 0,
        "idle_in_xact": 1,
        "idle_in_xact_aborted": 0,
        "fastpath": 0,
        "disabled": 0,
        "no_priv": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "active": 0,
        "waiting": 0,
        "idle": 0,
        "idle_in_xact": 0,
        "idle_in_xact_aborted": 0,
        "fastpath": 0,
        "disabled": 0,
        "no_priv": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "xacts": [
      {
        "dbname": "postgres",
        "current": {
          "n_commit": 172856,
          "n_rollback": 820
        },
        "measure_interval": 60.83692955970764,
        "n_commit": 218,
        "n_rollback": 1,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "current": {
          "n_commit": 2828,
          "n_rollback": 754
        },
        "measure_interval": 60.838372468948364,
        "n_commit": 3,
        "n_rollback": 1,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "locks": [
      {
        "dbname": "postgres",
        "access_share": 5,
        "waiting_access_share": 0,
        "row_share": 0,
        "waiting_row_share": 0,
        "row_exclusive": 0,
        "waiting_row_exclusive": 0,
        "share_update_exclusive": 0,
        "waiting_share_update_exclusive": 0,
        "share": 0,
        "waiting_share": 0,
        "share_row_exclusive": 0,
        "waiting_share_row_exclusive": 0,
        "exclusive": 0,
        "waiting_exclusive": 0,
        "access_exclusive": 0,
        "waiting_access_exclusive": 0,
        "siread": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "access_share": 0,
        "waiting_access_share": 0,
        "row_share": 0,
        "waiting_row_share": 0,
        "row_exclusive": 0,
        "waiting_row_exclusive": 0,
        "share_update_exclusive": 0,
        "waiting_share_update_exclusive": 0,
        "share": 0,
        "waiting_share": 0,
        "share_row_exclusive": 0,
        "waiting_share_row_exclusive": 0,
        "exclusive": 0,
        "waiting_exclusive": 0,
        "access_exclusive": 0,
        "waiting_access_exclusive": 0,
        "siread": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "blocks": [
      {
        "dbname": "postgres",
        "hitmiss_ratio": 99.99411937415002,
        "current": {
          "blks_read": 1243,
          "blks_hit": 21135963
        },
        "measure_interval": 60.83953022956848,
        "blks_read": 0,
        "blks_hit": 26956,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "hitmiss_ratio": 99.98406348143853,
        "current": {
          "blks_read": 819,
          "blks_hit": 5138321
        },
        "measure_interval": 60.84008240699768,
        "blks_read": 0,
        "blks_hit": 6779,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "bgwriter": [
      {
        "stats_reset": "2022-07-05T12:48:40.083954+00:00",
        "current": {
          "checkpoints_timed": 230,
          "checkpoints_req": 4,
          "checkpoint_write_time": 1347,
          "checkpoint_sync_time": 53,
          "buffers_checkpoint": 93,
          "buffers_clean": 0,
          "maxwritten_clean": 0,
          "buffers_backend": 7,
          "buffers_backend_fsync": 0,
          "buffers_alloc": 1860
        },
        "measure_interval": 60.84169578552246,
        "checkpoints_timed": 1,
        "checkpoints_req": 0,
        "checkpoint_write_time": 0,
        "checkpoint_sync_time": 0,
        "buffers_checkpoint": 0,
        "buffers_clean": 0,
        "maxwritten_clean": 0,
        "buffers_backend": 0,
        "buffers_backend_fsync": 0,
        "buffers_alloc": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "db_size": [
      {
        "dbname": "postgres",
        "size": 8823587,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "size": 8766243,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "tblspc_size": [
      {
        "spcname": "pg_default",
        "size": 26216521,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "spcname": "pg_global",
        "size": 573216,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "filesystems_size": [
        {
          "mount_point": "/",
          "device": "/dev/mapper/rl-root",
          "total": 14371782656,
          "used": 2755497984,
          "datetime": "2022-07-08T09:15:00.162294-04:00"
        },
        {
          "mount_point": "/boot",
          "device": "/dev/sda1",
          "total": 1063256064,
          "used": 203890688,
          "datetime": "2022-07-08T09:15:00.162294-04:00"
        }
    ],
    "cpu": [
      {
        "current": {
          "time_user": 92089650,
          "time_system": 32592590,
          "time_idle": 873267780,
          "time_iowait": 4131470,
          "time_steal": 0
        },
        "measure_interval": 60.825573682785034,
        "time_user": 47990,
        "time_system": 22530,
        "time_idle": 407810,
        "time_iowait": 4150,
        "time_steal": 0,
        "cpu": "global",
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "process": [
      {
        "procs_running": 6,
        "procs_blocked": 0,
        "procs_total": "2500",
        "current": {
          "context_switches": 1043767340,
          "forks": 1439465
        },
        "measure_interval": 60.826462507247925,
        "context_switches": 716632,
        "forks": 1123,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "memory": [
      {
        "mem_total": 16417996800,
        "mem_used": 15583711232,
        "mem_free": 834285568,
        "mem_buffers": 1217073152,
        "mem_cached": 4693979136,
        "swap_total": 0,
        "swap_used": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "loadavg": [
      {
        "load1": "2.23",
        "load5": "2.75",
        "load15": "2.33",
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "wal_files": [
      {
        "total": 2,
        "total_size": 33554432,
        "current_location": "0/50001C0",
        "archive_ready": 0,
        "current": {
          "written_size": 83886528
        },
        "measure_interval": 60.81913232803345,
        "written_size": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "replication_lag": [
      {
        "lag": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "temp_files_size_delta": [
      {
        "dbname": "postgres",
        "current": {
          "size": 0
        },
        "measure_interval": 60.812360763549805,
        "size": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "current": {
          "size": 0
        },
        "measure_interval": 60.806232213974,
        "size": 0,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "replication_connection": [
      {
        "upstream": "postgres0",
        "connected": 1,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "heap_bloat": [
      {
        "dbname": "postgres",
        "ratio": 5.555555555555555,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "ratio": 5.555555555555555,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ],
    "btree_bloat": [
      {
        "dbname": "postgres",
        "ratio": 10.602409638554217,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      },
      {
        "dbname": "template1",
        "ratio": 10.679611650485436,
        "datetime": "2022-07-08T10:38:57.857339+00:00"
      }
    ]
  },
  "version": "8.0.dev0"
}
""")


def test_open_metrics_from_data():
    from temboardagent.plugins.monitoring.db import (
        use_current_for_delta_metrics,
    )
    from temboardagent.plugins.monitoring.openmetrics import (
        generate_samples,
        format_open_metrics_lines,
    )
    data = use_current_for_delta_metrics(deepcopy(temboard_data))
    samples = generate_samples(data)
    text = "\n".join(format_open_metrics_lines(samples))

    assert 'pg_static{' in text
    assert 'temboard_agent_version="8.0' in text
    assert 'short_version="14.3"' in text

    assert 'node_context_switches_total ' in text
    assert 'node_cpu_seconds_total ' in text
    assert 'node_filesystem_free_bytes{device="/dev/mapper/rl-root",mountpoint="/"} 11616284672' in text  # noqa: E501
    assert 'node_filesystem_size_bytes{device="/dev/mapper/rl-root",mountpoint="/"} 14371782656' in text  # noqa: E501
    assert 'node_fork_total 1439465\n' in text
    assert 'node_load1 2.23' in text
    assert 'node_load15 2.33' in text
    assert 'node_load5 2.75' in text
    assert 'node_memory_Buffers_bytes 1217073152\n' in text
    assert 'node_memory_Cached_bytes 4693979136\n' in text
    assert 'node_memory_MemFree_bytes 834285568\n' in text
    assert 'node_memory_MemTotal_bytes 16417996800\n' in text
    assert 'node_memory_SwapFree_bytes 0\n' in text
    assert 'node_memory_SwapTotal_bytes 0\n' in text
    assert 'node_procs_blocked 0\n' in text
    assert 'node_procs_running 6\n' in text
    assert 'xnode_procs_total 2500\n' in text
