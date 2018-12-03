def test_envvars(mocker):
    mocker.patch('temboardui.configuration.os.environ', dict(PGHOST='0.0.0.0'))

    from temboardui.configuration import Configuration

    config = Configuration()

    assert '0.0.0.0' == config.repository['host']


def test_parsefile(mocker):
    open = mocker.patch('__builtin__.open')
    load = mocker.patch('temboardui.configuration.Configuration.load')
    readfp = mocker.patch('temboardui.configuration.Configuration.readfp')
    from temboardui.configuration import Configuration

    config = Configuration()
    config.parsefile('path/to/temboard.conf')

    assert 1 == open.call_count
    assert 1 == readfp.call_count
    assert 1 == load.call_count


def test_load():
    from StringIO import StringIO
    from temboardui.configuration import Configuration

    config = Configuration()
    config.configfile = '/path/to/temboard.conf'
    config.configdir = '/path/to'
    config.readfp(StringIO("""\
[temboard]
home = .

[logging]
"""))

    config.load()

    assert '.' == config.temboard['home']
