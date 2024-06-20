# Bridge temBoard and Prometheus
#
# - Configure Prometheus with a dedicated API key.
# - Refresh prometheus configuration on SIGHUP and every 5 minutes.
#
import glob
import logging
import os
import re
import signal
import subprocess
import time
from datetime import datetime, timedelta

import jinja2

import temboardui

from .model import Session, orm
from .toolkit import syncio

logger = logging.getLogger(__name__)


class Prometheus:
    name = "prometheus"

    def __init__(self, binpath, home):
        self.binpath = binpath
        self.home = home

    def __str__(self):
        return self.name

    # For services.BackgroundManager
    @property
    def pidfile(self):
        return f"{self.home}/{self}.pid"

    # For services.execute()
    def setup(self):
        os.chdir(self.home)

    @property
    def command(self):
        return [
            self.binpath,
            f"--config.file={self.home}/prometheus.yml",
            # 0.0.0.0 is reachable from dev grafana for testing purpose.
            # Once we embed alertmanager, use localhost.
            "--web.listen-address=0.0.0.0:8890",
            "--log.level=debug",
            "--storage.tsdb.retention.time=1h",
        ]


class Manager(syncio.Service):
    name = "prometheus manager"

    def __init__(self, app):
        self.app = app
        self.sighup = False
        self.provisionner = Provisionner(self.home)
        self.configuration_expiry = None
        # Set by services.BackgroundManager
        self.pid = None

    def trigger_reload(self):
        logger.debug("Triggering Prometheus configuration reload. pid=%s", self.pid)
        os.kill(self.pid, signal.SIGHUP)

    @property
    def home(self):
        return self.app.config.temboard.home + "/prometheus"

    # Interface for SignalMultiplexer
    def sighup_handler(self, *_):
        self.sighup = True

    # Interface for services.run
    def setup(self, sgm, bg):
        logger.info("Provisionning Prometheus in %s.", self.home)
        logger.debug("Creating temBoard API key.")
        session = Session()
        key = (
            orm.ApiKeys.insert(
                secret=orm.ApiKeys.generate_secret(),
                comment="temboard prometheus access",
            )
            .with_session(session)
            .scalar()
        )
        session.commit()

        self.provisionner.setup_global(key.secret)
        self._setup_instances()

        self.background = bg
        bg.add(Prometheus(self.app.config.monitoring.prometheus, self.home))
        sgm.register(bg)

    # Interface for syncio.Loop
    def accept(self):
        if self.configuration_expiry < datetime.utcnow():
            logger.debug("Prometheus configuration expired.")
            self._setup_instances()
            self.sighup = False

        if self.sighup:
            self.sighup = False
            self.app.reload()
            self._setup_instances()

        time.sleep(1)

    def _setup_instances(self):
        provisionner = Provisionner(self.home)
        provisionner.inspect()

        session = Session()
        for instance in session.execute(orm.Instances.all()):
            # DEPRECATED: SQAlchemy 1.4+ returns a tuple of objects
            if len(instance) == 1:
                (instance,) = instance

            if not instance.discover:
                logger.debug("Skipping unreached instance %s.", instance)
                continue
            provisionner.setup_instance(instance)

        provisionner.purge()

        self.configuration_expiry = datetime.utcnow() + timedelta(minutes=5)
        if hasattr(self, "background"):
            self.background.kill(signal.SIGHUP)


def find(binpath=None):
    candidates = [
        binpath,
        # Package path.
        "/usr/lib/temboard/prometheus",
        # Development path for CI.
        "ui/build/bin/prometheus",
    ]
    for binpath in candidates:
        if not binpath:
            continue
        if os.path.exists(binpath):
            return binpath


def version(binpath):
    if not binpath:
        return "n/a"
    out = subprocess.run([binpath, "--version"], stdout=subprocess.PIPE, check=True)
    m = re.search(r"version (\d+\.\d+\.\d+)", out.stdout.decode())
    if not m:
        logger.warning("Failed to parse Prometheus version from %s", out.stdout)
        return "n/a"
    return m.group(1)


class Provisionner:
    def __init__(self, home):
        self.home = home
        self.spurious_files = []

    def inspect(self):
        self.spurious_files = glob.glob(self.home + "/instances.d/instance-*.yml")

    def setup_global(self, apikey):
        os.makedirs(self.home + "/instances.d", exist_ok=True)
        t = jinja2.Template(
            source=PROMETHEUS_CONFIG_TEMPLATE,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )
        conf = t.render(
            apikey=apikey,
            home=self.home,
            now=datetime.utcnow(),
            temboard_version=temboardui.__version__,
        )
        with open(self.home + "/prometheus.yml", "w") as fo:
            os.chmod(fo.name, 0o600)
            fo.write(conf)

    def setup_instance(self, instance):
        path = "{}/instances.d/instance-{}-{}.scrape.yml".format(
            self.home, instance.agent_address, instance.agent_port
        )
        logger.debug(
            "Configuring Prometheus scaping. instance=%s file=%s",
            instance,
            os.path.basename(path),
        )
        t = jinja2.Template(
            source=INSTANCE_CONFIG_TEMPLATE,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )
        conf = t.render(
            instance=instance,
            now=datetime.utcnow(),
            temboard_version=temboardui.__version__,
        )
        with open(path, "w") as fo:
            os.chmod(fo.name, 0o600)
            fo.write(conf)
        if path in self.spurious_files:
            self.spurious_files.remove(path)
        return path

    def purge(self):
        for path in self.spurious_files:
            logger.debug("Purging configuration file %s.", os.path.basename(path))
            os.unlink(path)
        self.spurious_files = []


PROMETHEUS_CONFIG_TEMPLATE = """\
# This file is generated by temBoard. Do not edit.
#
# Generation Date: {{ now }}
# temBoard Version: {{ temboard_version }}
#
scrape_configs:
- job_name: temboard
  scrape_interval: 60s
  scheme: http
  authorization:
    type: Bearer
    credentials: "{{ apikey }}"
  file_sd_configs:
  - files:
    - instances.d/instance-*.yml
"""


INSTANCE_CONFIG_TEMPLATE = """\
# This file is generated by temBoard. Do not edit.
#
# Generation Date: {{ now }}
# temBoard Version: {{ temboard_version }}
#
- targets: [localhost:8888]
  labels:
    __metrics_path__: "/proxy/{{ instance.agent_address }}/{{ instance.agent_port }}/monitoring/metrics"
    instance:  "{{ instance.hostname }}:{{ instance.pg_port }}"
    agent:  "{{ instance.agent_address }}:{{ instance.agent_port }}"
"""  # noqa
