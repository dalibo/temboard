try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os.path

from temboardui.errors import ConfigurationError


class Configuration(configparser.ConfigParser):
    """
    Customized configuration parser.
    """
    def __init__(self, *args, **kwargs):
        configparser.ConfigParser.__init__(self, *args, **kwargs)
        # Default configuration values
        self.repository = {
            'host': os.environ.get('PGHOST', '/var/run/postgresql/'),
            'port': int(os.environ.get('PGPORT', '5432')),
            'user': os.environ.get('PGUSER', 'temboard'),
            'password': os.environ.get('PGPASSWORD', 'temboard'),
            'dbname': os.environ.get('PGDATABASE', 'temboard'),
        }

        self.plugins = {}

    def parsefile(self, configfile):
        self.configfile = os.path.realpath(configfile)
        self.configdir = os.path.dirname(self.configfile)

        try:
            with open(self.configfile) as fd:
                self.readfp(fd)
        except IOError:
            raise ConfigurationError("Configuration file %s can't be opened."
                                     % (self.configfile))
        except configparser.MissingSectionHeaderError:
            raise ConfigurationError(
                    "Configuration file does not contain section headers.")

        self.load()

    def load(self):
        try:
            self.repository['host'] = self.get('repository', 'host')
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        try:
            self.repository['user'] = self.get('repository', 'user')
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        try:
            if not (self.getint('repository', 'port') >= 0
                    and self.getint('repository', 'port') <= 65535):
                raise ValueError()
            self.repository['port'] = self.getint('repository', 'port')
        except ValueError:
            raise ConfigurationError(
                "'port' option must be an integer "
                "[0-65535] in 'repository' section in %s."
                % (self.configfile))
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        try:
            self.repository['password'] = self.get('repository', 'password')
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        try:
            self.repository['dbname'] = self.get('repository', 'dbname')
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass
