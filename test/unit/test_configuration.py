import pytest


def test_spec_and_value():
    from temboardagent.configuration import OptionSpec, Value

    spec = OptionSpec(section='temboard', name='verbose', default=False)
    assert repr(spec)

    value = Value('temboard_verbose', True, origin='test')
    assert repr(value)

    assert value.name in {spec}


def test_load(mocker):
    mocker.patch('temboardagent.configuration.Configuration')
    mocker.patch('temboardagent.configuration.MergedConfiguration.load_file')
    mocker.patch('temboardagent.configuration.load_plugins_configurations')

    from argparse import Namespace
    from temboardagent.configuration import OptionSpec, load_configuration

    specs = [
        OptionSpec(section='temboard', name='verbose', default=False),
    ]
    args = Namespace()
    config = load_configuration(specs=specs, args=args)

    assert config.temboard.verbose is False
    assert config.temboard.configfile.startswith('/etc/temboard-agent/')
    assert config.loaded is True

    args = Namespace(unkown=True)
    with pytest.raises(Exception):
        load_configuration(specs=specs, args=args)


def test_legacy(mocker):
    from temboardagent.configuration import MergedConfiguration, configparser

    configparser = configparser.RawConfigParser()
    configparser.temboard = {'port': 8080}
    configparser.configfile = 'configfile'
    configparser.confdir = 'confdir'
    config = MergedConfiguration()

    config.load_file(configparser)

    assert 8080 == config.temboard.port
    assert 'configfile' == config.configfile
    assert 'confdir' == config.confdir


def test_logging():
    from temboardagent.configuration import generate_logging_config, DotDict

    config = DotDict(dict(logging=dict(
        destination='pouet',
        facility='local0',
        method='stderr',
        level='DEBUG',
    )))

    generate_logging_config(**config)
