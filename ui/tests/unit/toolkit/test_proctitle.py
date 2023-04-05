from textwrap import dedent

import pytest


def test_resolve_main(mocker):
    from temboardui.toolkit.proctitle import compute_main_module_name

    mod = mocker.Mock(__package__='my', __name__='module')
    assert 'my.module' == compute_main_module_name(mod)

    mod = mocker.Mock(
        __package__='my', __name__='__main__', __file__='bla/module.py')
    assert 'my.module' == compute_main_module_name(mod)


def test_fix_argv(mocker):
    cmmn = mocker.patch(
        'temboardui.toolkit.proctitle.compute_main_module_name',
        autospec=True)
    from temboardui.toolkit.proctitle import fix_argv

    wanted = ['python', '-m', 'my.module']
    cmmn.return_value = 'my.module'
    input_ = ['python', '-m', '-m']
    assert wanted == fix_argv(input_)

    wanted = ['python', 'my-script.py']
    assert wanted == fix_argv(['python', 'my-script.py'])

    wanted = ['python', 'my-script.py', '-c', 'config']
    assert wanted == fix_argv(['python', 'my-script.py', '-c', 'config'])

    wanted = ['python', '-c', '__COMMAND_STRING__']
    assert wanted == fix_argv(['python', '-c', '-c'])


def test_read_memory():
    import ctypes

    from temboardui.toolkit.proctitle import read_byte

    data = ctypes.create_string_buffer(b'abcdef')
    b = read_byte(ctypes.addressof(data))
    assert 0x61 == b


def test_walk_bytes_backwards():
    import ctypes

    from temboardui.toolkit.proctitle import reverse_walk_memory

    data = ctypes.create_string_buffer(b'abcdef')
    address_of_nul = ctypes.addressof(data) + 6
    iterator = reverse_walk_memory(address_of_nul, limit=7)
    out = [b for _, b in iterator]
    wanted = list(b'\x00fedcba')
    assert wanted == out


def test_find_nulstrings():
    from temboardui.toolkit.proctitle import reverse_find_nulstring

    segment = b'\x00string0\x00string1\x00'
    bytes_ = ((0xbebed0d0, b) for b in reversed(segment))
    iterator = reverse_find_nulstring(bytes_)
    out = [b for _, b in iterator]
    wanted = ['string1', 'string0']
    assert wanted == out


def test_find_stack_segment():
    from temboardui.toolkit.proctitle import find_stack_segment_from_maps

    lines = dedent("""\
    55c7c8b2d000-55c7c8b35000 r-xp 00000000 fd:01 12582915                   /bin/lol
    55c7c9c82000-55c7c9ca3000 rw-p 00000000 00:00 0                          [heap]
    7feba95d1000-7feba9766000 r-xp 00000000 fd:01 2111422                    /lib/x86_64-linux-gnu/libc-2.24.so
    7feba9b95000-7feba9b96000 rw-p 00000000 00:00 0
    7fff737c3000-7fff737e5000 rw-p 00000000 00:00 0                          [stack]
    7fff737f9000-7fff737fb000 r--p 00000000 00:00 0                          [vvar]
    """).splitlines(True)  # noqa

    start, end = find_stack_segment_from_maps(lines)
    assert 0x7fff737c3000 == start
    assert 0x7fff737e5000 == end

    with pytest.raises(Exception):
        find_stack_segment_from_maps(lines=[])


def test_find_argv_from_procmaps_mod(mocker):
    mod = 'temboardui.toolkit.proctitle'
    fss = mocker.patch(mod + '.find_stack_segment_from_maps', autospec=True)
    mocker.patch(mod + '.reverse_walk_memory', autospec=True)
    rfn = mocker.patch(mod + '.reverse_find_nulstring', autospec=True)

    from temboardui.toolkit.proctitle import find_argv_memory_from_maps

    fss.return_value = 0xdeb, 0xf1
    rfn.return_value = reversed([
        # This is the nul-terminated of string in stack segment.
        (0xbad, 'garbadge'),
        (0x1c1, 'python'),
        (0xbad, '-m'),
        (0xbad, 'temboard.script.tool'),
        (0xbad, 'LC_ALL=fr_FR.UTF-8'),
        (0xbad, '/usr/lib/python3.6/site-packages/...'),
    ])

    argv = ['python', '-m', 'temboard.script.tool']
    env = dict(LC_ALL='fr_FR.UTF-8')
    _, address = find_argv_memory_from_maps(maps=None, argv=argv, environ=env)
    assert 0x1c1 == address


def test_find_argv_from_procmaps_command_string(mocker):
    mod = 'temboardui.toolkit.proctitle'
    fss = mocker.patch(mod + '.find_stack_segment_from_maps', autospec=True)
    mocker.patch(mod + '.reverse_walk_memory', autospec=True)
    rfn = mocker.patch(mod + '.reverse_find_nulstring', autospec=True)

    from temboardui.toolkit.proctitle import find_argv_memory_from_maps

    fss.return_value = 0xdeb, 0xf1
    rfn.return_value = reversed([
        # This is the nul-terminated of string in stack segment.
        (0xbad, 'garbadge'),
        (0x1c1, 'python'),
        (0xbad, '-c'),
        (0xbad, 'from module import main; main()'),
        (0xbad, 'LC_ALL=fr_FR.UTF-8'),
        (0xbad, '/usr/lib/python3.6/site-packages/...'),
    ])

    argv = ['python', '-c', '__COMMAND_STRING__']
    env = dict(LC_ALL='fr_FR.UTF-8')
    _, address = find_argv_memory_from_maps(maps=None, argv=argv, environ=env)
    assert 0x1c1 == address


def test_set_proc_title(mocker):
    memmove = mocker.patch(
        'temboardui.toolkit.proctitle.ctypes.memmove', autospec=True)
    from temboardui.toolkit.proctitle import ProcTitleManager

    setproctitle = ProcTitleManager(prefix='prefix: ')
    title = setproctitle('not initialized')
    assert title is None

    setproctitle.address = 0xd0d0bebe
    setproctitle.size = 24
    memmove.reset_mock()
    title = setproctitle('title')
    assert title.startswith(b'prefix: title\0')
    assert 24 == len(title)
    assert memmove.called is True
