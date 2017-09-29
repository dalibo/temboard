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
        # to test argument parsing
        OptionSpec(section='temboard', name='fromarg', default='DEFVAL'),
        # to test environment parsing
        OptionSpec(section='temboard', name='fromenv', default='DEFVAL'),
        # to test default value
        OptionSpec(section='temboard', name='fromdefault', default='DEFVAL'),
    ]
    args = Namespace(temboard_fromarg='ARGVAL')
    environ = dict(
        TEMBOARD_FROMENV='ENVVAL',
        # These should be ignored
        TEMBOARD_FROMARG='ENVAL',
        PATH='',
    )
    config = load_configuration(specs=specs, args=args, environ=environ)

    assert 'DEFVAL' == config.temboard.fromdefault
    assert 'ARGVAL' == config.temboard.fromarg
    assert 'ENVVAL' == config.temboard.fromenv
    assert config.temboard.configfile.startswith('/etc/temboard-agent/')
    assert config.loaded is True


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
