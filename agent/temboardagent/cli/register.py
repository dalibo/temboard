import os
import logging
import socket
import sys
from getpass import getpass
from textwrap import dedent
from sys import stdout
from urllib.error import HTTPError
from urllib.parse import urlparse

from ..errors import UserError
from ..toolkit.app import SubCommand
from ..toolkit.http import TemboardClient
from ..tools import validate_parameters
from .app import app


try:
    input = raw_input
except NameError:
    pass

logger = logging.getLogger(__name__)
T_USERNAME = b'(^[a-z0-9]{3,16}$)'
T_PASSWORD = b'(^.{5,32}$)'


@app.command
class Register(SubCommand):
    """Register a PostgreSQL instance to a temBoard UI."""

    def define_arguments(self, parser):
        parser.description = dedent("""\

        This command is interactive. register will ask you username and
        password to call temBoard UI API.

        """)

        parser.add_argument(
            '--host',
            dest='host',
            help="Agent address accessible from UI. Default: %(default)s",
            default=socket.getfqdn(),
        )
        self.app.config_specs['temboard_port'].add_argument(
            parser, '-p', '--port',
            help="Agent listening TCP port. Default: %(default)s",
        )
        parser.add_argument(
            '-g', '--groups',
            dest='groups',
            help="Instance groups list, comma separated. Default: %(default)s",
            default=None,
        )
        parser.add_argument(
            '--ui-url',
            dest='temboard_ui_url',
            metavar='URL',
            help="temBoard UI address to register to.",
        )
        super(Register, self).define_arguments(parser)

    def main(self, args):
        agent_hostport = "%s:%s" % (args.host, self.app.config.temboard.port)
        agent_baseurl = "https://%s" % agent_hostport

        logger.info("Working for agent listening at %s.", agent_baseurl)

        agentclient = TemboardClient.factory(
            self.app.config,
            args.host, self.app.config.temboard.port,
        )
        ui_url_raw = self.app.config.temboard.ui_url.rstrip('/')
        ui_url = urlparse(ui_url_raw)
        uiclient = TemboardClient.factory(
            self.app.config,
            scheme=ui_url.scheme, host=ui_url.hostname, port=ui_url.port,
        )

        try:
            # Getting system/instance informations using agent's discovering
            # API.
            logger.info("Discovering system and PostgreSQL ...")
            response = agentclient.get('/discover')
            response.raise_for_status()
            discover = response.json()
            logger.info(
                "temBoard agent for %s instance serving %s on port %s.",
                discover['postgres']['version_summary'],
                discover['postgres']['data_directory'],
                discover['postgres']['port'],
            )
        except OSError as e:
            logger.error("Failed to connect to agent: %s", e)
            logger.error("Is agent %s running?", agent_hostport)
            raise UserError("Connection failure.")
        except TemboardClient.Error as e:
            raise UserError(str(e))

        groups = args.groups
        if groups:
            groups = args.groups.split(',')
        else:
            logger.warning("Instance without groups are hidden in UI!")

        try:
            logger.info("Verifying signing key.")
            response = uiclient.get(ui_url.path + '/signing.key')
            response.raise_for_status()
            wanted = response.read()
            with open(self.app.config.temboard.signing_public_key, 'rb') as fo:
                configured = fo.read()

            if wanted != configured:
                logger.error(
                    "Agent %s is not configured with UI %s signing key.",
                    agent_hostport, ui_url.netloc,
                )
                logger.error(
                    "Use temboard-agent fetch-key --force "
                    "to accept %s signing key.",
                    ui_url.netloc,
                )
                raise UserError("Signature mismatch.")
        except OSError as e:
            logger.error("Failed to connect to UI: %s", e)
            logger.error("Is UI %s running?", ui_url.netloc)
            raise UserError("Connection failure.")
        except TemboardClient.Error as e:
            raise UserError("UI returned error: %s" % e)

        try:
            logger.info("Login at %s ...", ui_url_raw)
            username = ask_username()
            password = ask_password()
        except EOFError:
            # Write new line after prompt.
            sys.stderr.write("\n")
            raise UserError("Exiting.")

        try:
            response = uiclient.post(
                ui_url.path + '/json/login',
                {'username': username, 'password': password},
            )
            response.raise_for_status()

            # POSTing new instance
            logger.info("Registering instance/agent in %s ...", ui_url_raw)
            path = ui_url.path + '/json/register/instance'
            response = uiclient.post(path, {
                'agent_key': app.config.temboard['key'],
                'agent_address': args.host,
                'agent_port': str(app.config.temboard['port']),
                'discover': discover,
                # Loosely reuse agent plugin as UI plugins.
                'plugins': discover['temboard']['plugins'],
                'groups': groups
            })
            response.raise_for_status()
            dashboard_url = ui_url_raw + '/server/%s/%s/dashboard' % (
                args.host, self.app.config.temboard.port,
            )
            logger.info(
                "Instance registered. Managed it at %s.", dashboard_url)
        except TemboardClient.Error as e:
            raise UserError("UI returned error: %s" % e)

        return 0


def ask_password():
    try:
        raw_pass = os.environ['TEMBOARD_UI_PASSWORD']
    except KeyError:
        raw_pass = getpass(" Password: ")

    try:
        password = raw_pass
        validate_parameters({'password': password},
                            [('password', T_PASSWORD, False)])
    except HTTPError:
        stdout.write("Invalid password.\n")
        return ask_password()
    return password


def ask_username():
    try:
        raw_username = os.environ['TEMBOARD_UI_USER']
    except KeyError:
        raw_username = input(" Username: ")

    try:
        username = raw_username
        validate_parameters({'username': username},
                            [('username', T_USERNAME, False)])
    except HTTPError:
        stdout.write("Invalid username.\n")
        return ask_username()
    return username
