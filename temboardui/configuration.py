try:
    import configparser
except ImportError:
     import ConfigParser as configparser

import os
import json
import re
from temboardui.errors import ConfigurationError
from temboardui.logger import LOG_FACILITIES, LOG_LEVELS, LOG_METHODS

class Configuration(configparser.ConfigParser):
    """
    Customized configuration parser.
    """
    def __init__(self, configfile, *args, **kwargs):
        configparser.ConfigParser.__init__(self, *args, **kwargs)
        self.configfile = configfile
        # Default configuration values
        self.temboard = {
            'port': 8888,
            'address': '0.0.0.0',
            'ssl_cert_file': None,
            'ssl_key_file': None,
            'ssl_ca_cert_file': None,
            'cookie_secret': None,
            'plugins': ["dashboard", "settings", "activity", "supervision"],
            'plugins_orm_engine': ["supervision"],
            'home': '/var/run/temboard'
        }
        self.logging = {
            'method': 'syslog',
            'facility': 'local0',
            'destination': '/dev/log',
            'level': 'INFO'
        }
        self.repository = {
            'host': 'localhost',
            'user': 'temboard',
            'port': 5432,
            'password': 'temboard',
            'dbname': 'temboard'
        }

        self.plugins = {}

        try:
            with open(self.configfile) as fd:
                self.readfp(fd)
        except IOError as e:
            raise ConfigurationError("Configuration file %s can't be opened."
                    % (self.configfile))
        except configparser.MissingSectionHeaderError as e:
            raise ConfigurationError(
                    "Configuration file does not contain section headers.")

        # Test if 'temboard' section exists.
        self.check_section('temboard')

        try:
            if not (self.getint('temboard', 'port') >= 0
                    and self.getint('temboard', 'port') <= 65535):
                raise ValueError()
            self.temboard['port'] = self.getint('temboard', 'port')
        except ValueError as e:
            raise ConfigurationError("'port' option must be an integer [0-65535] in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass
        try:
            if not re.match(r'(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)(\.(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)){3}$', \
                self.get('temboard', 'address')):
                raise ValueError()
            self.temboard['address'] = self.get('temboard', 'address')
        except ValueError as e:
            raise ConfigurationError("'address' option must be a valid IPv4 in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass

        try:
            with open(self.get('temboard', 'ssl_cert_file')) as fd:
                _ = fd.read()
                self.temboard['ssl_cert_file'] = self.get('temboard', 'ssl_cert_file')
        except Exception as e:
            raise ConfigurationError("SSL certificate file %s can't be opened."
                    % (self.get('temboard', 'ssl_cert_file')))
        except configparser.NoOptionError as e:
           pass

        try:
            with open(self.get('temboard', 'ssl_key_file')) as fd:
                _ = fd.read()
                self.temboard['ssl_key_file'] = self.get('temboard', 'ssl_key_file')
        except Exception as e:
            raise ConfigurationError("SSL private key file %s can't be opened."
                    % (self.get('temboard', 'ssl_key_file')))
        except configparser.NoOptionError as e:
           pass

        try:
            with open(self.get('temboard', 'ssl_ca_cert_file')) as fd:
                _ = fd.read()
                self.temboard['ssl_ca_cert_file'] = self.get('temboard', 'ssl_ca_cert_file')
        except Exception as e:
            raise ConfigurationError("SSL CA cert file %s can't be opened."
                    % (self.get('temboard', 'ssl_ca_cert_file')))
        except configparser.NoOptionError as e:
           pass

        try:
            if not re.match(r'.{10,128}$', \
                self.get('temboard', 'cookie_secret')):
                raise ValueError()
            val = self.get('temboard', 'cookie_secret').lstrip('"').rstrip('"')
            self.temboard['cookie_secret'] = val
        except ValueError as e:
            raise ConfigurationError("'cookie_secret' parameter must be a valid string (.{10,128}) in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass

        try:
            plugins = json.loads(self.get('temboard', 'plugins'))
            if not type(plugins) == list:
                raise ValueError()
            for plugin in plugins:
                if not re.match('^[a-zA-Z0-9]+$', str(plugin)):
                    raise ValueError
            self.temboard['plugins'] = plugins
        except configparser.NoOptionError as e:
           pass
        except ValueError as e:
            raise ConfigurationError("'plugins' option must be a list of string"
                    " (alphanum only) in %s"
                    % (self.configfile))

        try:
            plugins = json.loads(self.get('temboard', 'plugins_orm_engine'))
            if not type(plugins) == list:
                raise ValueError()
            for plugin in plugins:
                if not re.match('^[a-zA-Z0-9]+$', str(plugin)):
                    raise ValueError
            self.temboard['plugins_orm_engine'] = plugins
        except configparser.NoOptionError as e:
           pass
        except ValueError as e:
            raise ConfigurationError("'plugins_orm_engine' option must be a list of string"
                    " (alphanum only) in %s"
                    % (self.configfile))

        try:
            home = self.get('temboard', 'home')
            if not os.access(home, os.W_OK):
                raise Exception()
            self.temboard['home'] = self.get('temboard', 'home')
        except Exception as e:
            raise ConfigurationError("Home directory %s not writable."
                    % (self.get('temboard', 'home')))
        except configparser.NoOptionError as e:
           pass


        # Test if 'logging' section exists.
        self.check_section('logging')
        try:
            if not self.get('logging', 'method') in LOG_METHODS:
                raise ValueError()
            self.logging['method'] = self.get('logging', 'method')
        except ValueError as e:
            raise ConfigurationError("Invalid 'method' option in 'logging' section in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass
        try:
            if not self.get('logging', 'facility') in LOG_FACILITIES:
                raise ValueError()
            self.logging['facility'] = self.get('logging', 'facility')
        except ValueError as e:
            raise ConfigurationError("Invalid 'facility' option in 'logging' section in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass
        try:
            self.logging['destination'] = self.get('logging', 'destination')
        except configparser.NoOptionError as e:
           pass
        try:
            if not self.get('logging', 'level') in LOG_LEVELS:
                raise ValueError()
            self.logging['level'] = self.get('logging', 'level')
        except ValueError as e:
            raise ConfigurationError("Invalid 'level' option in 'logging' section in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass

        # Test if 'repository' section exists.
        self.check_section('repository')
        try:
            self.repository['host'] = self.get('repository', 'host')
        except configparser.NoOptionError as e:
           pass

        try:
            self.repository['user'] = self.get('repository', 'user')
        except configparser.NoOptionError as e:
           pass

        try:
            if not (self.getint('repository', 'port') >= 0
                    and self.getint('repository', 'port') <= 65535):
                raise ValueError()
            self.repository['port'] = self.getint('repository', 'port')
        except ValueError as e:
            raise ConfigurationError("'port' option must be an integer "
                    "[0-65535] in 'repository' section in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass

        try:
            self.repository['password'] = self.get('repository', 'password')
        except configparser.NoOptionError as e:
           pass

        try:
            self.repository['dbname'] = self.get('repository', 'dbname')
        except configparser.NoOptionError as e:
           pass

    def check_section(self, section):
        if not self.has_section(section):
            raise ConfigurationError(
                    "Section '%s' not found in configuration file %s"
                    % (section, self.configfile))
