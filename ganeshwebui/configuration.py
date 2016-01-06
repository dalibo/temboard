try:
    import configparser
except ImportError:
     import ConfigParser as configparser

import os
import json
import re
from ganeshwebui.errors import ConfigurationError
from ganeshwebui.logger import LOG_FACILITIES, LOG_LEVELS, LOG_METHODS

class Configuration(configparser.ConfigParser):
    """
    Customized configuration parser.
    """ 
    def __init__(self, configfile, *args, **kwargs):
        configparser.ConfigParser.__init__(self, *args, **kwargs)
        self.configfile = configfile
        # Default configuration values
        self.ganesh = {
            'port': 443,
            'address': '0.0.0.0',
            'ssl_cert_file': None,
            'ssl_key_file': None,
            'ssl_ca_cert_file': None,
            'cookie_secret': None,
            'plugins': [],
            'plugins_orm_engine': []
        }
        self.logging = {
            'method': 'syslog',
            'facility': 'local0',
            'destination': '/dev/log',
            'level': 'INFO'
        }
        self.repository = {
            'host': '/var/run/postgresql',
            'user': 'ganesh',
            'port': 5432,
            'password': 'ganesh',
            'dbname': 'ganesh'
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

        # Test if 'ganesh' section exists.
        self.check_section('ganesh')

        try:
            if not (self.getint('ganesh', 'port') >= 0
                    and self.getint('ganesh', 'port') <= 65535):
                raise ValueError()
            self.ganesh['port'] = self.getint('ganesh', 'port')
        except ValueError as e:
            raise ConfigurationError("'port' option must be an integer [0-65535] in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass
        try:
            if not re.match(r'(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)(\.(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)){3}$', \
                self.get('ganesh', 'address')):
                raise ValueError()
            self.ganesh['address'] = self.get('ganesh', 'address')
        except ValueError as e:
            raise ConfigurationError("'address' option must be a valid IPv4 in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass

        try:
            with open(self.get('ganesh', 'ssl_cert_file')) as fd:
                _ = fd.read()
                self.ganesh['ssl_cert_file'] = self.get('ganesh', 'ssl_cert_file')
        except Exception as e:
            raise ConfigurationError("SSL certificate file %s can't be opened."
                    % (self.get('ganesh', 'ssl_cert_file')))
        except configparser.NoOptionError as e:
           pass

        try:
            with open(self.get('ganesh', 'ssl_key_file')) as fd:
                _ = fd.read()
                self.ganesh['ssl_key_file'] = self.get('ganesh', 'ssl_key_file')
        except Exception as e:
            raise ConfigurationError("SSL private key file %s can't be opened."
                    % (self.get('ganesh', 'ssl_key_file')))
        except configparser.NoOptionError as e:
           pass

        try:
            with open(self.get('ganesh', 'ssl_ca_cert_file')) as fd:
                _ = fd.read()
                self.ganesh['ssl_ca_cert_file'] = self.get('ganesh', 'ssl_ca_cert_file')
        except Exception as e:
            raise ConfigurationError("SSL CA cert file %s can't be opened."
                    % (self.get('ganesh', 'ssl_ca_cert_file')))
        except configparser.NoOptionError as e:
           pass

        try:
            if not re.match(r'.{10,128}$', \
                self.get('ganesh', 'cookie_secret')):
                raise ValueError()
            val = self.get('ganesh', 'cookie_secret').lstrip('"').rstrip('"')
            self.ganesh['cookie_secret'] = val
        except ValueError as e:
            raise ConfigurationError("'cookie_secret' parameter must be a valid string (.{10,128}) in %s."
                    % (self.configfile))
        except configparser.NoOptionError as e:
           pass

        try:
            plugins = json.loads(self.get('ganesh', 'plugins'))
            if not type(plugins) == list:
                raise ValueError()
            for plugin in plugins:
                if not re.match('^[a-zA-Z0-9]+$', str(plugin)):
                    raise ValueError
            self.ganesh['plugins'] = plugins
        except configparser.NoOptionError as e:
           pass
        except ValueError as e:
            raise ConfigurationError("'plugins' option must be a list of string"
                    " (alphanum only) in %s"
                    % (self.configfile))

        try:
            plugins = json.loads(self.get('ganesh', 'plugins_orm_engine'))
            if not type(plugins) == list:
                raise ValueError()
            for plugin in plugins:
                if not re.match('^[a-zA-Z0-9]+$', str(plugin)):
                    raise ValueError
            self.ganesh['plugins_orm_engine'] = plugins
        except configparser.NoOptionError as e:
           pass
        except ValueError as e:
            raise ConfigurationError("'plugins_orm_engine' option must be a list of string"
                    " (alphanum only) in %s"
                    % (self.configfile))


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
