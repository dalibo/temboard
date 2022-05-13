import logging
from sys import stdout
from getpass import getpass

from ..errors import ConfigurationError, HTTPError, UserError
from ..toolkit.app import BaseApplication
from ..toolkit.app import define_core_arguments
from ..tools import validate_parameters
from ..types import T_PASSWORD, T_USERNAME
from ..usermgmt import get_user
from ..usermgmt import hash_password
from ..version import __version__
from ..cli.app import list_options_specs


logger = logging.getLogger(__name__)


try:
    input = raw_input
except NameError:
    pass


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
    raw_username = input("Username: ")
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


class AddUserApplication(BaseApplication):
    PROGRAM = "temboard-agent-adduser"
    VERSION = __version__

    DEFAULT_CONFIGFILES = [
        '/etc/temboard-agent/temboard-agent.conf',
        'temboard-agent.conf',
    ]

    def main(self, argv, environ):
        parser = self.create_parser(
            description="Add a new temboard-agent user.",
        )
        define_core_arguments(parser, appversion=self.VERSION)
        args = parser.parse_args(argv)
        self.bootstrap(args=args, environ=environ)

        logger.info("Using file %s.", self.config.temboard.users)
        # Load configuration from the configuration file.
        username = ask_username(self.config)
        password = ask_password()
        hash_ = hash_password(username, password).decode('utf-8')
        try:
            with open(self.config.temboard.users, 'a') as fd:
                fd.write("{}:{}\n".format(username, hash_))
        except OSError as e:
            raise UserError(str(e))
        else:
            stdout.write("Done.\n")


main = AddUserApplication(specs=list_options_specs(), with_plugins=False)

if __name__ == '__main__':
    main()
