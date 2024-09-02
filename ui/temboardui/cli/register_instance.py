import json
import logging
import os.path
import sys

from ..agentclient import TemboardAgentClient
from ..model import Session, orm
from ..toolkit import validators as v
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..toolkit.utils import JSONEncoder
from .app import app

logger = logging.getLogger(__name__)


@app.command
class RegisterInstance(SubCommand):
    """Out-of-bound registration of a PostgreSQL instance."""

    name = "register-instance"

    def define_arguments(self, parser):
        parser.add_argument(
            "--comment",
            default="Registered from CLI.",
            help="Instance comment. Default: %(default)s",
        )

        parser.add_argument(
            "--notify",
            action="store_true",
            default=False,
            help="Whether to contact users on monitoring alert.",
        )

        parser.add_argument(
            "--if-not-exists",
            action="store_true",
            dest="skip_existing",
            default=False,
            help="Don't fail if agent is already registered.",
        )

        parser.add_argument(
            "-e",
            "--environment",
            dest="environment",
            default="",
            help="Instance environment name.",
        )

        parser.add_argument(
            "-p",
            "--plugins",
            dest="plugins",
            default="",
            help=(
                "Activate this temBoard UI plugins, comma separated. "
                "Defaults to agent's plugins."
            ),
        )

        parser.add_argument(
            "agent_address", metavar="ADDR", help="temBoard agent listenning address"
        )

        parser.add_argument(
            "agent_port",
            metavar="PORT",
            nargs="?",
            default=2345,
            type=int,
            help="temBoard agent listenning port",
        )

        super().define_arguments(parser)

    def main(self, args):
        agent = f"{args.agent_address}:{args.agent_port}"

        if not args.environment:
            raise UserError("Missing environment. Use --environment to define.")

        plugins = v.commalist(args.plugins)
        for plugin in plugins:
            if plugin not in self.app.config.temboard.plugins:
                raise UserError("Plugin %s is not loaded." % plugin)

        session = Session()
        logger.debug("Check for existing instance.")
        instance = (
            orm.Instance.get(
                agent_address=args.agent_address, agent_port=args.agent_port
            )
            .with_session(session)
            .one_or_none()
        )

        if instance:
            if not args.skip_existing:
                raise UserError(
                    "Instance %s:%s already registered."
                    % (instance.hostname, instance.pg_port)
                )
            else:
                logger.warning(
                    "Instance %s:%s already registered. Skipping.",
                    instance.hostname,
                    instance.pg_port,
                )
                self.output_instance(instance)
                logger.info("Browse instance at %s.", instance.dashboard_url(self.app))
                return 0

        logger.info("Discovering temBoard agent at %s.", agent)
        client = TemboardAgentClient.factory(
            self.app.config, args.agent_address, args.agent_port
        )
        try:
            response = client.get("/discover")
            response.raise_for_status()
        except OSError as e:
            logger.error("Failed to discover agent at %s: %s", agent, e)
            raise UserError(
                "Can't connect to agent. "
                "Please check address and port or that agent is running."
            )
        except client.Error as e:
            raise UserError("temBoard Agent error: %s" % e)
        else:
            discover = response.json()
            discover_etag = response.headers["ETag"]

        if "signature_status" not in discover:
            logger.error("Legacy agent does not support out of band registration.")
            logger.error("Please upgrade agent or use web UI.")
            raise UserError("Legacy agent registration refused")

        if "valid" != discover["signature_status"]:
            logger.error(
                "Agent %s is configured for another UI or " "signing key is outdated.",
                agent,
            )
            logger.error("Update signing key with temboard-agent fetch-key.")
            raise UserError("Signature missmatch")

        logger.info(
            "Registering %s serving %s at %s:%s.",
            discover["postgres"]["version_summary"],
            discover["postgres"]["data_directory"],
            discover["system"]["hostname"],
            discover["postgres"]["port"],
        )
        if plugins:
            for plugin in plugins:
                if plugin not in discover["temboard"]["plugins"]:
                    raise UserError("Plugin %s disabled on agent side." % plugin)
        else:
            plugins = guess_default_plugins(
                ui_plugins=self.app.config.temboard.plugins,
                agent_plugins=discover["temboard"]["plugins"],
            )
        logger.debug("Enabling plugins %s.", ", ".join(plugins))

        environment = session.execute(orm.Environment.get(args.environment)).fetchone()
        instance = (
            orm.Instance.insert(
                agent_address=args.agent_address,
                agent_port=args.agent_port,
                discover=discover,
                discover_etag=discover_etag,
                notify=args.notify,
                comment=args.comment,
                environment=environment,
            )
            .with_session(session)
            .one()
        )

        for plugin in plugins:
            session.execute(instance.enable_plugin(plugin))

        session.commit()
        logger.info("Instance successfully registered.")

        logger.debug("Fast-collect monitoring metrics.")
        if os.path.exists(self.app.scheduler.scheduler.address):
            if "monitoring" in plugins:
                from ..plugins.monitoring import collector

                logger.info("Schedule monitoring collect for agent now.")
                collector.defer(
                    self.app, address=instance.agent_address, port=instance.agent_port
                )

            if "statements" in plugins:
                from ..plugins.statements import statements_pull1

                logger.info("Schedule statements collect for agent now.")
                statements_pull1.defer(
                    self.app, host=instance.agent_address, port=instance.agent_port
                )
        else:
            logger.info(
                "Scheduler is not running." "Start temBoard server to collect metrics."
            )

        self.output_instance(instance)

        logger.info("Browse instance at %s.", instance.dashboard_url(self.app))

    def output_instance(self, instance):
        json.dump(instance.asdict(), sys.stdout, indent="  ", cls=JSONEncoder)
        sys.stdout.write(os.linesep)


def guess_default_plugins(ui_plugins, agent_plugins):
    # Select all plugins enabled in both UI and agent.
    return set(ui_plugins) & set(agent_plugins)
