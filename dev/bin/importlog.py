#!/usr/bin/env python
#
# Documented in docs/howto-performances.md
#

import logging
import math
import os
import pdb
import sys
from bdb import BdbQuit
from datetime import datetime, timedelta, timezone
from subprocess import check_call
from textwrap import dedent

import httpx
import pytz

logger = logging.getLogger("importlog")
LOCALTZ = pytz.timezone("UTC")
KNOWN_LABELS = [
    "agent",
    "pid",
    "service",
    "task",
    "dbname",
    "spcname",
    "timestamp",
    "method",
    "url",
    "status",
    "handler",
    "plugin",
]
KNOWN_METRICS = {
    "fork": dict(
        type="counter", unit="nounit", help="Count of total fork by the process."
    ),
    "io_rchar": dict(
        type="counter", unit="bytes", help="Total bytes read by the process."
    ),
    "io_wchar": dict(
        type="counter", unit="bytes", help="Total bytes written by the process."
    ),
    "load1": dict(type="gauge", unit="nounit", help="1m load average"),
    "load5": dict(type="gauge", unit="nounit", help="5m load average"),
    "load15": dict(type="gauge", unit="nounit", help="15m load average"),
    "vsize": dict(
        type="gauge", unit="bytes", help="Total memory usage of the process."
    ),
    "stime": dict(
        type="counter",
        unit="seconds",
        help="Total seconds spent by the process in kernel space.",
    ),
    "utime": dict(
        type="counter",
        unit="seconds",
        help="Total seconds spent by the process in userspace.",
    ),
    # Agent metrics
    "xacts_n_commit": dict(
        type="counter", unit="nounit", help="Total commit in database."
    ),
    "xacts_n_rollback": dict(
        type="counter", unit="nounit", help="Total commit in database."
    ),
    # HTTP metric
    "response_time": dict(type="gauge", unit="seconds", help="HTTP response time"),
}


def main(logfile):
    global LOCALTZ

    log_count = 0
    point_count = 0
    start = None

    labels = dict(
        job="logsender.py",
        logfile="%s_%s" % (datetime.now().strftime("%Y%m%dT%H%M%S"), logfile),
    )
    logger.info("Analyzing %s.", logfile)

    LOCALTZ = find_timezone()

    loki_batch = []
    epoch_ns = None
    prev_epoch_s = None
    with open(logfile) as fo, open("dev/prometheus/import/data.txt", "w") as metrics_fo:
        omw = OpenMetricsWriter(metrics_fo, KNOWN_METRICS)
        for line in fo:
            if not line.startswith("20"):
                logger.warning("Skip malformed line: %r.", line)
                if epoch_ns:
                    loki_batch.append(("%d" % epoch_ns, line.rstrip()))
                continue

            # log line format:
            #
            #     YYYY-mm-dd HH:MM:SS,SSSSSS command[PID]: [MODULE  ] LEVEL: MESSAGE...  # noqa
            #
            # or systemd:
            #
            #     YYYY-mm-ddTHH:MM:SS+ZZZZ hostname env[PID]: MESSAGE...
            if "T" == line[10]:  # journalctl
                dateTtime, tail = line.split(" ", 1)
                date, time = dateTtime.split("T")
            else:
                date, time, tail = line.split(" ", 2)

            try:
                timestamp = parse_datetime(date, time)
            except Exception as e:
                logger.warning("Failed to parse datetime: %s.", e)
                logger.warning("Malformed line: %s.", line)
                continue
            epoch_s = timestamp.timestamp()
            epoch_ns = epoch_s * 1_000_000_000
            epoch_s = math.floor(epoch_s)

            if not start:
                start = timestamp

            # TODO: étiquetter PID
            loki_batch.append(("%d" % epoch_ns, line.rstrip()))

            if len(loki_batch) >= 100:
                send_log_batch_to_loki(loki_batch, labels=labels)
                log_count += len(loki_batch)
                loki_batch[:] = []

            # UI output contains agent metrics. This may mess with out of order
            # sample.
            if " agent=" in tail:
                logger.warning("Skipping agent metrics.")
                continue

            if " io_rchar=" in tail or " up=1 " in tail or " method=" in tail:
                # Accept a single sample per second.
                if prev_epoch_s and prev_epoch_s == epoch_s:
                    logger.warning(
                        "Skipping duplicated sample: timestamp=%s %s.",
                        epoch_s,
                        tail.strip(),
                    )
                    continue
                prev_epoch_s = epoch_s

                # métriques
                _, _, message = tail.partition(":")
                try:
                    metrics = dict(parse_logfmt(message))
                except Exception as e:
                    logger.warning("Failed to parse perf metrics: %s.", e)
                    logger.warning("Malformed line: %s.", line)
                    continue

                for name, value in metrics.items():
                    if name in KNOWN_LABELS:
                        continue

                    local_labels = labels.copy()
                    local_labels.update(
                        dict((k, metrics[k]) for k in KNOWN_LABELS if k in metrics)
                    )
                    omw.append(name, local_labels, value, epoch_s)
                point_count += 1
        omw.close()

    end = timestamp

    if loki_batch:
        send_log_batch_to_loki(loki_batch, labels)
        log_count += len(loki_batch)

    logger.info("Parsed messages from %s to %s.", start, end)
    logger.info("Log time span is %s.", end - start)
    logger.info("Exported %s points in OpenMetrics format.", point_count)
    logger.info("Inserted %s log messages in Loki.", log_count)
    logger.info("Backfilling Prometheus from OpenMetrics.")
    check_call(
        [
            "docker",
            "compose",
            "exec",
            "prometheus",
            "promtool",
            "tsdb",
            "create-blocks-from",
            "openmetrics",
            "/import/data.txt",
            "/prometheus",
        ]
    )

    from_ = 1000 * int(min(start.timestamp(), omw.start) - 60)
    to = 1000 * int(max(end.timestamp(), omw.end) + 60)
    dashboard_url = (
        "http://0.0.0.0:3000"
        "/d/MkhXLKbnz/temboard-performance"
        f"?orgId=1&from={from_}&to={to}"
        f"&var-service=.%2B&var-logfile={labels['logfile']}"
    )
    logger.info("View graph and messages at: %s.", dashboard_url)


def send_log_batch_to_loki(lines, labels):
    # cf. https://grafana.com/docs/loki/latest/api/#post-lokiapiv1push
    logger.info("Sending %s lines to loki. %s", len(lines), labels)
    r = httpx.post(
        "http://0.0.0.0:3100/loki/api/v1/push",
        json=dict(streams=[dict(stream=labels, values=lines)]),
    )
    if r.status_code >= 400:
        logger.error("Loki error: %s", r.content.decode())


def parse_logfmt(raw):
    for metric in raw.split():
        name, value = metric.split("=")
        try:
            if "." in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            pass
        yield name, value


def parse_datetime(date, time):
    dt = datetime(
        year=int(date[:4]),
        month=int(date[5:7]),
        day=int(date[8:]),
        hour=int(time[:2]),
        minute=int(time[3:5]),
        second=int(time[6:8]),
    )

    if "+" == time[8]:  # journalctl timezone offset
        offset = int(time[9:])
        tz = timezone(timedelta(hours=int(offset / 100), minutes=offset % 100))
        return dt.replace(tzinfo=tz)
    else:
        dt = dt.replace(microsecond=int(time[9:]))
        return LOCALTZ.localize(dt)


def find_timezone():
    try:
        name = os.environ["TIMEZONE"]
        logger.info("Read timezone from env: %s.", name)
    except KeyError:
        with open("/etc/timezone") as fo:
            name = fo.read().strip()

        logger.info("Read timezone from /etc: %s.", name)

    return pytz.timezone(name)


class OpenMetricsWriter:
    blacklist = ["up"]

    def __init__(self, fo, known_metrics):
        self.fo = fo
        self.known_metrics = known_metrics
        self.unknown = []
        self.declared_metrics = set()
        self.start = None
        self.end = None

    def append(self, name, labels, value, epoch_s):
        if name in self.blacklist:
            return
        if name in self.unknown:
            return
        if name not in self.known_metrics:
            logger.debug("Unknown metric %s", name)
            self.unknown.append(name)
            return
        unit = self.known_metrics[name]["unit"]
        metric = name
        if unit != "nounit":
            metric += "_" + unit
        if name not in self.declared_metrics:
            self.fo.write(
                dedent(f"""\
            # HELP {metric} {self.known_metrics[name]['help']}
            # TYPE {metric} {self.known_metrics[name]['type']}
            """)
            )
            if unit != "nounit":
                self.fo.write(
                    dedent(f"""\
                # UNIT {metric} {unit}
                """)
                )
            self.declared_metrics.add(name)

        if "timestamp" in labels:
            # Overwrite epoch from pseudo label timestamp
            timestamp = labels.pop("timestamp")
            date, time = timestamp.split("T")
            timestamp = parse_datetime(date, time)
            epoch_s = timestamp.timestamp()
        self.start = min(self.start or epoch_s, epoch_s)

        labels = ",".join('%s="%s"' % label for label in labels.items())
        self.fo.write(
            dedent(f"""\
        {metric}{{{labels}}} {value} {epoch_s:.0f}
        """)
        )
        self.end = epoch_s

    def close(self):
        self.fo.write("# EOF\n")
        for name in self.unknown:
            logger.debug("Unknown metric %s.", name)


if "http_proxy" in os.environ:
    # http_proxy will likely break loki requests.
    del os.environ["http_proxy"]

logging.basicConfig(level=logging.DEBUG, format="%(levelname)1.1s: %(message)s")
try:
    sys.exit(main(*sys.argv[1:]) or 0)
except BdbQuit:
    logger.error("Graceful exit from debugger.")
except Exception:
    logger.exception("Unhandled error:")
    pdb.post_mortem(sys.exc_info()[-1])
    sys.exit(1)
