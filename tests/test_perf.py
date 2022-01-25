def test_format():
    from sampleproject.toolkit.perf import PerfCounters

    p = PerfCounters()

    p['a'] = 1
    p['bc'] = 1
    p['ba'] = 1

    assert 'a=1 ba=1 bc=1' in str(p)


def test_stat():
    from sampleproject.toolkit.perf import PerfCounters

    p = PerfCounters()

    p.snapshot()

    assert 'io_rchar' in p
    assert 'io_wchar' in p
