import os
import logging
import socket
from getpass import getpass
from textwrap import dedent
from sys import stdout
from urllib.error import HTTPError
from urllib.parse import urlparse

from ..errors import UserError
from ..toolkit.app import SubCommand
from ..toolkit.http import TemboardClient
from ..tools import validate_parameters
from ..types import T_PASSWORD, T_USERNAME
from .app import app


try:
    input = raw_input
except NameError:
    pass

logger = logging.getLogger(__name__)


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
        agent_baseurl = "https://{}:{}".format(
            args.host, self.app.config.temboard.port)

        logger.info("Working for agent listening at %s.", agent_baseurl)

        agentclient = TemboardClient.factory(
            self.app.config,
            args.host, self.app.config.temboard.port,
        )
        ui_url_raw = self.app.config.temboard.ui_url.rstrip('/')
        ui_url = urlparse(ui_url_raw)
        uiclient = TemboardClient.factory(
            self.app.config, ui_url.hostname, ui_url.port,
        )

        try:
            # Getting system/instance informations using agent's discovering
            # API.
            logger.info("Discovering system and PostgreSQL ...")
            response = agentclient.get('/discover')
            response.raise_for_status()
            infos = response.json()

            logger.info(
                "temboard agent for %s instance at %s listening on port %s.",
                infos['pg_version_summary'],
                infos['pg_data'], infos['pg_port'],
            )

            logger.info("Login at %s ...", ui_url_raw)
            username = ask_username()
            password = ask_password()
            response = uiclient.post(
                ui_url.path + '/json/login',
                {'username': username, 'password': password},
            )
            response.raise_for_status()

            groups = args.groups
            if groups:
                groups = args.groups.split(',')

            # POSTing new instance
            logger.info(
                "Registering instance/agent in %s ...", ui_url_raw)
            path = ui_url.path + '/json/register/instance'
            response = uiclient.post(
                path,
                {
                    'hostname': infos['hostname'],
                    'agent_key': app.config.temboard['key'],
                    'agent_address': args.host,
                    'agent_port': str(app.config.temboard['port']),
                    'cpu': infos['cpu'],
                    'memory_size': infos['memory_size'],
                    'pg_port': infos['pg_port'],
                    'pg_data': infos['pg_data'],
                    'pg_version': infos['pg_version'],
                    'pg_version_summary': infos['pg_version_summary'],
                    'plugins': infos['plugins'],
                    'groups': groups
                },
            )
            response.raise_for_status()
            dashboard_url = ui_url_raw + '/server/%s/%s/dashboard' % (
                args.host, self.app.config.temboard.port,
            )
            logger.info(
                "Instance registered. Managed it at %s.", dashboard_url)
        except TemboardClient.Error as e:
            raise UserError(str(e))

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
