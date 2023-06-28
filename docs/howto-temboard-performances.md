temBoard UI has a built-in, logfmt based, performances tracing. You enable
performance tracing, execute temBoard UI and analyze the logs afterward using a
development grafana setup.


## Enabling performance tracing

Define the `PERF` environment variable in temBoard UI execution environment.
With systemd, create a directory `/etc/systemd/system/temboard.service.d/` and
put the following content in the `enable-perf-tracing.conf` drop-in file:

``` conf
[Service]
Environment=PERF=y
```

Ensure logging level is set to DEBUG in `/etc/temboard/temboard.conf`:

``` conf

[logging]
method = stderr
level = DEBUG

```

Reload systemd with `systemctl daemon-reload`. Restart temBoard with `systemctl
restart temboard`.

You will see the following `perf` messages in temBoard logs.

```
...
2022-01-27 12:35:36,257 [2673406] [taskmanager     ] DEBUG: Activate worker purge_data_worker
2022-01-27 12:35:36,260 [2673427] [services        ]  INFO: Starting worker pool.
2022-01-27 12:35:36,261 [2673406] [services        ]  INFO: Starting web.
2022-01-27 12:35:36,262 [2673427] [perf            ] DEBUG: Scheduling perf counters each 15 seconds.
2022-01-27 12:35:36,262 [2673428] [services        ]  INFO: Starting scheduler.
2022-01-27 12:35:36,262 [2673406] [perf            ] DEBUG: Scheduling perf counters each 15 seconds.
2022-01-27 12:35:36,263 [2673427] [perf            ] DEBUG: io_rchar=0 io_wchar=184 pid=2673427 service=worker-pool stime=0.0 utime=0.0 vsize=116420608
2022-01-27 12:35:36,263 [2673406] [perf            ] DEBUG: io_rchar=9610041 io_wchar=108165 pid=2673406 service=web stime=0.05 utime=0.66 vsize=116420608
2022-01-27 12:35:36,263 [2673427] [services        ] DEBUG: Entering worker pool loop.
2022-01-27 12:35:36,263 [2673428] [perf            ] DEBUG: Scheduling perf counters each 15 seconds.
2022-01-27 12:35:36,263 [2673428] [perf            ] DEBUG: io_rchar=0 io_wchar=182 pid=2673428 service=scheduler stime=0.0 utime=0.0 vsize=116420608
2022-01-27 12:35:36,264 [2673428] [taskmanager     ] DEBUG: Update Task aggregate_data with options={}
...
```

To export logs from journald, use the following command:

``` console
# journalctl -u temboard --utc --output=short-iso --since '-30 minutes'
```

Adapt `--since` argument to your needs.


## Visualize with Grafana

To visualize temBoard's performances traces, the development environment of
temBoard ships et Grafana setup with Prometheus and Loki. See
[Contributing](CONTRIBUTING.md) to setup a development environment.
`dev/importlog.py` Python script backfills Prometheus and Loki from temBoard
traces file.

``` console
$ docker-compose up -d
$ ./dev/importlog.py my-temboard.log
I: Analyzing systemd.log.
I: Read timezone from /etc: Europe/Paris.
...
D: HTTP Request: POST http://0.0.0.0:3100/loki/api/v1/push "HTTP/1.1 204 No Content"
I: Parsed messages from 2022-01-27 15:09:54+01:00 to 2022-01-27 18:03:15+01:00.
I: Log time span is 2:53:21.
I: Exported 1209 points in OpenMetrics format.
I: Inserted 18742 log messages in Loki.
I: Backfilling Prometheus from OpenMetrics.
BLOCK ULID                  MIN TIME       MAX TIME       DURATION      NUM SAMPLES  NUM CHUNKS   NUM SERIES   SIZE
01FTE7W2G0CGHM0GZQFYP2KD0Z  1643294766000  1643299198001  1h13m52.001s  1643         1086         1086         117422
01FTE7W2J70EJATMMGAXHHDP09  1643299209000  1643302995001  1h3m6.001s   4484         3476         3476         372009
I: View graph and messages at: http://0.0.0.0:3000/d/MkhXLKbnz/temboard-performance?orgId=1&from=1643292534000&to=1643303055000&var-logfile=systemd.log.
$
```

Follow the final link to see the dashboard narrowed to the date interval
corresponding to log messages dates and filtered to the named log file.

Please take advise:

- Avoid reusing the same file name for multiple temBoard logs.
- Avoid reimporting a log file.
- Avoid importing file **newer** than 3 hours. Loki and Prometheus backfilling
  is not very consistent with hot data.
- Grafana may need a few minutes to show you labels and points right after
  imports. Be patient.

If you need to restart from scratch, just trash the compose setup and restart.

``` console
$ docker-compose down -v
Stopping perfui_prometheus_1 ... done
Stopping perfui_loki_1       ... done
Stopping perfui_grafana_1    ... done
Removing perfui_prometheus_1 ... done
Removing perfui_loki_1       ... done
Removing perfui_grafana_1    ... done
Removing network perfui_default
Removing volume perfui_grafana-data
$ make develop
...
```
