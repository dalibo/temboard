# -*- coding: utf-8 -*-
from mock import Mock


def test_multiline_formatter():
    from logging import makeLogRecord
    from temboardui.logger import MultilineFormatter

    formatter = MultilineFormatter(fmt='PREFIX: %(message)s')
    record = makeLogRecord({
        'msg': (
            u"Line0 ékçeption\n"
            "Line1"
        ),
        'exc_text': (
            "Traceback (most recent call last):\n"
            'File "/usr/local/src/temboard/temboard", line 6, in <module>\n'
            "  exec(compile(open(__file__).read(), __file__, 'exec'))\n"
        )
    })

    payload = formatter.format(record)

    assert 'PREFIX: Line0' in payload
    assert 'PREFIX: Line1' in payload
    assert 'PREFIX: Traceback' in payload
    assert 'PREFIX: File' in payload
    assert 'PREFIX:   exec' in payload


def test_config():
    from temboardui.logger import generate_logging_config

    config = Mock(logging=dict(
        destination='destination',
        facility='local0',
        method='stderr',
        level='INFO',
    ))

    logging = generate_logging_config(config)

    assert logging['loggers']['temboardui']['level'] == config.logging['level']
    assert 'StreamHandler' in logging['handlers']['configured']['()']
