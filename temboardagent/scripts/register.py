from __future__ import unicode_literals

from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
import os
from sys import stdout
from getpass import getpass
import re
import json
import logging

from ..cli import Application
from ..errors import (
    HTTPError,
    UserError,
)
from ..types import T_PASSWORD, T_USERNAME
from ..toolkit.app import define_core_arguments
from ..tools import validate_parameters
from ..httpsclient import https_request
from .agent import list_options_specs


try:
    input = raw_input
except NameError:
    pass

logger = logging.getLogger(__name__)


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


def define_arguments(parser):
    define_core_arguments(parser, appversion=Application.VERSION)

    parser.add_argument(
        '-?', '--help',
        action='help',
        help='show this help message and exit')

    parser.add_argument(
        '-h', '--host',
        dest='temboard_address',
        help="Agent address. Default: %(default)s",
    )
    parser.add_argument(
        '-p', '--port',
        dest='temboard_port', type=int,
        help="Agent listening TCP port. Default: %(default)s",
    )
    parser.add_argument(
        '-g', '--groups',
        dest='groups',
        help="Instance groups list, comma separated. Default: %(default)s",
        default=None,
    )
    parser.add_argument(
        'ui_address',
        metavar='TEMBOARD-UI-ADDRESS',
        help="temBoard UI address to register to.",
    )


class RegisterApplication(Application):
    PROGRAM = "temboard-agent-register"

    def main(self, argv, environ):
        parser = ArgumentParser(
            prog='temboard-agent-register',
            description=(
                "Register a couple PostgreSQL instance/agent "
                "to a temBoard UI."
            ),
            add_help=False,
            argument_default=UNDEFINED_ARGUMENT,
        )
        define_arguments(parser)
        args = parser.parse_args(argv)
        self.bootstrap(args=args, environ=environ)
        return wrapped_main(args, self)


def wrapped_main(args, app):
    # Load configuration from the configuration file.
    try:
        # Getting system/instance informations using agent's discovering API
        url = "https://%(address)s:%(port)s/discover" % app.config['temboard']
        print("Getting system & PostgreSQL informations from the agent "
              "(%s) ..." % (url,))
        (code, content, cookies) = https_request(
            None,
            'GET',
            url,
            headers={
                "Content-type": "application/json"
            }
        )
        infos = json.loads(content)

        print("Login at %s ..." % (args.ui_address))
        username = ask_username()
        password = ask_password()
        (code, content, cookies) = https_request(
            None,
            'POST',
            "%s/json/login" % (args.ui_address.rstrip('/')),
            headers={
                "Content-type": "application/json"
            },
            data={'username': username, 'password': password}
        )
        temboard_cookie = None
        for cookie in cookies.split("\n"):
            cookie_content = cookie.split(";")[0]
            if re.match(r'^temboard=.*$', cookie_content):
                temboard_cookie = cookie_content
                continue

        if args.groups:
            groups = [g for g in args.groups.split(',')]
        else:
            groups = None

        # POSTing new instance
        print("Registering instance/agent to %s ..." % (args.ui_address))
        (code, content, cookies) = https_request(
            None,
            'POST',
            "%s/json/register/instance" % (args.ui_address.rstrip('/')),
            headers={
                "Content-type": "application/json",
                "Cookie": temboard_cookie
            },
            data={
                'hostname': infos['hostname'],
                'agent_key': app.config.temboard['key'],
                'agent_address': app.config.temboard['address'],
                'agent_port': str(app.config.temboard['port']),
                'cpu': infos['cpu'],
                'memory_size': infos['memory_size'],
                'pg_port': infos['pg_port'],
                'pg_data': infos['pg_data'],
                'pg_version': infos['pg_version'],
                'pg_version_summary': infos['pg_version_summary'],
                'plugins': infos['plugins'],
                'groups': groups
            }
        )
        if code != 200:
            raise HTTPError(code, content)
        print("Done.")
    except UserError:
        raise
    except HTTPError as e:
        err = json.loads(e.read())
        raise UserError(err['error'])
    except Exception as e:
        raise UserError(str(e) or repr(e))

    return 0


main = RegisterApplication(specs=list_options_specs(), with_plugins=False)

if __name__ == '__main__':  # pragma: no cover
    main()
