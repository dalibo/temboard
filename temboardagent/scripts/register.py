from __future__ import unicode_literals

from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
import os
from sys import stdout, stderr
from getpass import getpass
import re
import urllib2
import json
import logging

from ..cli import cli, define_common_arguments
from ..errors import (
    ConfigurationError,
    HTTPError,
)
from ..types import T_PASSWORD, T_USERNAME
from ..tools import validate_parameters
from ..httpsclient import https_request
from ..configuration import load_configuration, setup_logging
from agent import list_options_specs

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
        raw_username = raw_input(" Username: ")

    try:
        username = raw_username
        validate_parameters({'username': username},
                            [('username', T_USERNAME, False)])
    except HTTPError:
        stdout.write("Invalid username.\n")
        return ask_username()
    return username


def define_arguments(parser):
    parser.add_argument(
        '-?', '--help',
        action='help',
        help='show this help message and exit')

    define_common_arguments(parser)

    parser.add_argument(
        '-h', '--host',
        dest='host',
        help="Agent address. Default: %(default)s",
        default='localhost'
    )
    parser.add_argument(
        '-p', '--port',
        dest='port',
        help="Agent listening TCP port. Default: %(default)s",
        default='2345',
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


@cli
def main(argv, environ):
    parser = ArgumentParser(
        prog='temboard-agent-register',
        description=(
            "Register a couple PostgreSQL instance/agent "
            "to a Temboard UI."
        ),
        add_help=False,
        argument_default=UNDEFINED_ARGUMENT,
    )
    define_arguments(parser)

    args = parser.parse_args(argv)

    setup_logging(level='ERROR')

    # Loading agent configuration file.
    config = load_configuration(
        specs=list_options_specs(),
        args=args, environ=environ,
    )
    config.setup_logging()

    # Load configuration from the configuration file.
    try:
        # Getting system/instance informations using agent's discovering API
        print("Getting system & PostgreSQL informations from the agent "
              "(https://%s:%s/discover) ..." % (args.host, args.port))
        (code, content, cookies) = https_request(
                None,
                'GET',
                "https://%s:%s/discover" % (args.host, args.port),
                headers={
                    "Content-type": "application/json"
                })
        infos = json.loads(content)

        print("Login at %s ..." % (args.ui_address))
        username = ask_username()
        password = ask_password()
        (code, content, cookies) = https_request(
                None,
                'POST',
                "%s/json/login" % (args.ui_address),
                headers={
                    "Content-type": "application/json"
                },
                data={'username': username, 'password': password})
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
                "%s/json/register/instance" % (args.ui_address),
                headers={
                    "Content-type": "application/json",
                    "Cookie": temboard_cookie
                },
                data={
                    'hostname': infos['hostname'],
                    'agent_key': config.temboard['key'],
                    'agent_address': args.host,
                    'agent_port': str(config.temboard['port']),
                    'cpu': infos['cpu'],
                    'memory_size': infos['memory_size'],
                    'pg_port': infos['pg_port'],
                    'pg_data': infos['pg_data'],
                    'pg_version': infos['pg_version'],
                    'plugins': infos['plugins'],
                    'groups': groups
                })
        if code != 200:
            raise HTTPError(code, content)
        print("Done.")
    except (ConfigurationError, HTTPError, Exception) as e:
        if isinstance(e, urllib2.HTTPError):
            err = json.loads(e.read())
            stderr.write("FATAL: %s\n" % err['error'])
        else:
            stderr.write("FATAL: %s\n" % str(e))
        return 1

    return 0


if __name__ == '__main__':  # pragma: no cover
    main()
