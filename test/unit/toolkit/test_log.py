def test_temboard_debug(mocker):
    mocker.patch('temboardagent.toolkit.log.sys.stderr.isatty')

    from temboardagent.toolkit.log import generate_logging_config

    config = generate_logging_config()
    assert 'minimal' == config['handlers']['configured']['formatter']

    config = generate_logging_config(level='DEBUG', debug=False)

    assert 'verbose' == config['handlers']['configured']['formatter']
    assert 'DEBUG' == config['loggers']['temboardagent']['level']

    config = generate_logging_config(level='INFO', debug=True)

    assert 'verbose' == config['handlers']['configured']['formatter']
    assert 'DEBUG' == config['loggers']['temboardagent']['level']

    config = generate_logging_config(level='INFO', debug=b'__debug__')

    assert 'verbose' == config['handlers']['configured']['formatter']
    assert 'DEBUG' == config['loggers']['temboardagent']['level']


def test_limit_debug():
    from temboardagent.toolkit.log import generate_logging_config

    config = generate_logging_config(
        level='INFO', debug='myplugins,temboardagent.cli')

    assert 'INFO' == config['loggers']['temboardagent']['level']
    assert 'DEBUG' == config['loggers']['myplugins']['level']
    assert 'DEBUG' == config['loggers']['temboardagent.cli']['level']
