import logging
import os.path
import json
import sys

from .app import app
from ..agentclient import TemboardAgentClient
from ..application import (
    add_instance,
    check_agent_address,
    get_instance,
)
from ..model import Session
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..toolkit import validators as v
from ..toolkit.utils import JSONEncoder
from ..handlers.settings.instance import (
    add_instance_in_groups,
    enable_instance_plugins,
)
from ..plugins.monitoring import collector
from ..plugins.statements import statements_pull1

logger = logging.getLogger(__name__)


@app.command
class RegisterInstance(SubCommand):
    """Out-of-bound registration of a PostgreSQL instance.

    """

    name = 'register-instance'

    def define_arguments(self, parser):
        parser.add_argument(
            '--comment',
            default="Registered from CLI.",
            help="Instance comment. Default: %(default)s"
        )

        parser.add_argument(
            '--notify',
            action='store_true', default=False,
            help="Whether to contact users on monitoring alert."
        )

        parser.add_argument(
            '--if-not-exists',
            action='store_true', dest='skip_existing', default=False,
            help="Don't fail if agent is already registered."
        )

        parser.add_argument(
            '-g', '--groups',
            dest='groups', default='',
            help="Instance groups list, comma separated.",
        )

        parser.add_argument(
            '-p', '--plugins',
            dest='plugins', default='',
            help=(
                "Activate this temBoard UI plugins, comma separated. "
                "Defaults to agent's plugins.")
        )

        parser.add_argument(
            'agent_address', metavar='ADDR',
            help="temBoard agent listenning address",
        )

        parser.add_argument(
            'agent_port', metavar='PORT', nargs='?', default=2345, type=int,
            help="temBoard agent listenning port",
        )

        super(RegisterInstance, self).define_arguments(parser)

    def main(self, args):
        groups = v.commalist(args.groups)
        if not groups:
            raise UserError("Missing instance groups. Use --groups to define.")
        plugins = v.commalist(args.plugins)
        for plugin in plugins:
            if plugin not in self.app.config.temboard.plugins:
                raise UserError("Plugin %s is not loaded." % plugin)

        try:
            check_agent_address(args.agent_address)
        except Exception as e:
            raise UserError(str(e))

        agent = "%s:%s" % (args.agent_address, args.agent_port)

        session = Session()
        logger.debug("Check for existing instance.")
        instance = get_instance(session, args.agent_address, args.agent_port)
        if instance:
            if not args.skip_existing:
                raise UserError("Instance %s:%s already registered." % (
                    instance.hostname, instance.pg_port))
            else:
                logger.warning(
                    "Instance %s:%s already registered. Skipping.",
                    instance.hostname, instance.pg_port,
                )
                self.output_instance(instance)
                logger.info(
                    "Browse instance at %s.", instance.dashboard_url(self.app))
                return 0

        logger.info("Discovering temBoard agent at %s.", agent)
        client = TemboardAgentClient.factory(
            self.app.config,
            args.agent_address, args.agent_port,
        )
        try:
            response = client.get('/discover')
            response.raise_for_status()
        except OSError as e:
            logger.error(
                "Failed to discover agent at %s: %s", agent, e)
            raise UserError(
                "Can't connect to agent. "
                "Please check address and port or that agent is running.")
        except client.Error as e:
            raise UserError("temBoard Agent error: %s" % e)
        else:
            discover = response.json()
            discover_etag = response.headers['ETag']

        if 'signature_status' not in discover:
            logger.error(
                "Legacy agent does not support out of band registration.")
            logger.error("Please upgrade agent or use web UI.")
            raise UserError("Legacy agent registration refused")

        if 'valid' != discover['signature_status']:
            logger.error(
                "Agent %s is configured for another UI or "
                "signing key is outdated.", agent)
            logger.error("Update signing key with temboard-agent fetch-key.")
            raise UserError("Signature missmatch")

        logger.info(
            "Registering %s serving %s at %s:%s.",
            discover['postgres']['version_summary'],
            discover['postgres']['data_directory'],
            discover['system']['hostname'],
            discover['postgres']['port'],
        )
        data = {}
        data['new_agent_address'] = args.agent_address
        data['new_agent_port'] = args.agent_port
        data['comment'] = args.comment
        data['notify'] = args.notify
        data['discover'] = discover
        data['discover_etag'] = discover_etag

        if plugins:
            for plugin in plugins:
                if plugin not in discover['temboard']['plugins']:
                    raise UserError(
                        "Plugin %s disabled on agent side." % plugin)
        else:
            plugins = guess_default_plugins(
                ui_plugins=self.app.config.temboard.plugins,
                agent_plugins=discover['temboard']['plugins'],
            )
        logger.debug("Enabling plugins %s.", ', '.join(plugins))

        instance = add_instance(session, **data)
        session.add(instance)
        session.flush()  # Get an Instance.id
        add_instance_in_groups(session, instance, groups)
        enable_instance_plugins(
            session, instance, plugins, self.app.config.temboard.plugins,
        )
        session.commit()
        logger.info("Instance successfully registered.")

        logger.debug("Fast-collect monitoring metrics.")
        if os.path.exists(self.app.scheduler.scheduler.address):
            if 'monitoring' in plugins:
                logger.info("Schedule monitoring collect for agent now.")
                collector.defer(
                    self.app,
                    address=data['new_agent_address'],
                    port=data['new_agent_port'],
                )

            if 'statements' in plugins:
                logger.info("Schedule statements collect for agent now.")
                statements_pull1.defer(
                    self.app,
                    host=data['new_agent_address'],
                    port=data['new_agent_port'],
                )
        else:
            logger.info(
                "Scheduler is not running."
                "Start temBoard server to collect metrics.")

        self.output_instance(instance)

        logger.info("Browse instance at %s.", instance.dashboard_url(self.app))

    def output_instance(self, instance):
        json.dump(instance.asdict(), sys.stdout, indent="  ", cls=JSONEncoder)
        sys.stdout.write(os.linesep)


def guess_default_plugins(ui_plugins, agent_plugins):
    # Select all plugins enabled in both UI and agent.
    return set(ui_plugins) & set(agent_plugins)
