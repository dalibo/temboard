def test_color(mocker):
    import logging
    from sampleproject.toolkit.log import ColoredStreamHandler

    handler = ColoredStreamHandler()
    record = logging.getLogger().makeRecord(
        name='toto', level=logging.DEBUG,
        fn='toto.py', lno=42,
        msg='Message', args=(),
        exc_info=None,
    )
    s = handler.format(record)
    assert '\033[0m' in s
    assert 'Message' in s


def test_multiline(mocker):
    import logging
    from sampleproject.toolkit.log import MultilineFormatter

    formatter = MultilineFormatter('PREFIX: %(message)s')
    record = logging.getLogger().makeRecord(
        name='toto', level=logging.DEBUG,
        fn='toto.py', lno=42,
        msg='Line1\nLine2', args=(),
        exc_info=None,
    )
    s = formatter.format(record)

    assert 'PREFIX: Line1' in s
    assert 'PREFIX: Line2' in s

    record.msg = 'Single'
    s = formatter.format(record)
    assert 'PREFIX: Single' in s


def test_lastname():
    import logging
    from sampleproject.toolkit.log import LastnameFilter

    filter_ = LastnameFilter()
    record = logging.getLogger().makeRecord(
        name='toto', level=logging.DEBUG,
        fn='toto.py', lno=42,
        msg='Message', args=(),
        exc_info=None,
    )
    ret = filter_.filter(record)
    assert ret
    assert 'toto' == record.lastname

    record.name = 'sampleproject.titi'
    ret = filter_.filter(record)
    assert 'titi' == record.lastname


def test_temboard_debug(mocker):
    mocker.patch('sampleproject.toolkit.log.sys.stderr.isatty')

    from sampleproject.toolkit.log import generate_logging_config

    config = generate_logging_config()
    assert 'minimal' == config['handlers']['configured']['formatter']

    config = generate_logging_config(level='DEBUG', debug=False)

    assert 'verbose' == config['handlers']['configured']['formatter']
    assert 'DEBUG' == config['loggers']['sampleproject']['level']

    config = generate_logging_config(level='INFO', debug=True)

    assert 'verbose' == config['handlers']['configured']['formatter']
    assert 'DEBUG' == config['loggers']['sampleproject']['level']

    config = generate_logging_config(level='INFO', debug='__debug__')

    assert 'verbose' == config['handlers']['configured']['formatter']
    assert 'DEBUG' == config['loggers']['sampleproject']['level']


def test_limit_debug():
    from sampleproject.toolkit.log import generate_logging_config

    config = generate_logging_config(
        level='INFO', debug='myplugins,sampleproject.cli')

    assert 'INFO' == config['loggers']['sampleproject']['level']
    assert 'DEBUG' == config['loggers']['myplugins']['level']
    assert 'DEBUG' == config['loggers']['sampleproject.cli']['level']


def test_setup(mocker):
    dc = mocker.patch('sampleproject.toolkit.log.dictConfig', autospec=True)
    from sampleproject.toolkit.log import setup_logging
    setup_logging()
    assert dc.called is True
