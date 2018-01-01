# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
from sys import stdout
from getpass import getpass

from ..cli import cli, define_common_arguments
from ..usermgmt import hash_password
from ..errors import ConfigurationError, HTTPError, UserError
from ..usermgmt import get_user
from ..configuration import load_configuration
from ..types import T_PASSWORD, T_USERNAME
from ..tools import validate_parameters
from .agent import list_options_specs


def ask_password():
    raw_pass1 = getpass("Password: ")
    raw_pass2 = getpass("Retype password: ")
    if raw_pass1 != raw_pass2:
        stdout.write("Sorry, passwords do not match.\n")
        return ask_password()
    try:
        password = raw_pass1
        validate_parameters({'password': password},
                            [('password', T_PASSWORD, False)])
    except HTTPError:
        stdout.write("Invalid password.\n")
        return ask_password()
    return password


def ask_username(config):
    stdout.write("Username: ".encode('utf-8'))
    raw_username = raw_input()
    try:
        get_user(config.temboard['users'], raw_username)
    except HTTPError:
        pass
    except ConfigurationError:
        pass
    else:
        stdout.write("User already exists.\n")
        return ask_username(config)
    try:
        username = raw_username
        validate_parameters({'username': username},
                            [('username', T_USERNAME, False)])
    except HTTPError:
        stdout.write("Invalid username.\n")
        return ask_username(config)
    return username


@cli
def main(argv, environ):
    parser = ArgumentParser(
        prog='temboard-agent-adduser',
        description="Add a new temboard-agent user.",
        argument_default=UNDEFINED_ARGUMENT,
    )
    define_common_arguments(parser)
    args = parser.parse_args(argv)
    config = load_configuration(
        specs=list_options_specs(), args=args, environ=environ,
    )

    # Load configuration from the configuration file.
    username = ask_username(config)
    password = ask_password()
    hash_ = hash_password(username, password).decode('utf-8')
    try:
        with open(config.temboard['users'], 'a') as fd:
            fd.write("%s:%s\n" % (username, hash_))
    except IOError as e:
        raise UserError(str(e))
    else:
        stdout.write("Done.\n")


if __name__ == '__main__':
    main()
