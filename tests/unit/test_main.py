def test_arguments():
    from argparse import ArgumentParser
    from temboardui.__main__ import define_arguments

    parser = ArgumentParser()
    define_arguments(parser)

    args = parser.parse_args(['--pid-file', 'my.pid'])

    assert 'my.pid' == args.temboard_pidfile
