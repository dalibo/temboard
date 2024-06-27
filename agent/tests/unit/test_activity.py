from textwrap import dedent


def test_parse_proc_stat():
    from temboardagent.plugins.activity import parse_proc_stat

    contents = dedent("""\
    336567 (bash) S 4324 336567 336567 34828 345175 4194304 13474 104206 0 11 12 6 116 44 20 0 1 0 9732774 20516864 4224 18446744073709551615 94122439303168 94122440068253 140731111635664 0 0 0 65536 3686404 1266761467 0 0 0 17 3 0 0 0 0 0 94122440303280 94122440351044 94122444668928 140731111638810 140731111638816 140731111638816 140731111641070 0
    """)  # noqa

    values = parse_proc_stat(contents)
    assert 12 == values["utime"]
    assert 6 == values["stime"]
    assert 116 == values["cutime"]
    assert 44 == values["cstime"]


def test_parse_proc_human_status():
    from temboardagent.plugins.activity import parse_proc_human

    # From man 5 proc
    contents = dedent("""\
    Name:   bash
    Umask:  0022
    State:  S (sleeping)
    Tgid:   17248
    Ngid:   0
    Pid:    17248
    PPid:   17200
    TracerPid:      0
    Uid:    1000    1000    1000    1000
    Gid:    100     100     100     100
    FDSize: 256
    Groups: 16 33 100
    NStgid: 17248
    NSpid:  17248
    NSpgid: 17248
    NSsid:  17200
    VmPeak:     131168 kB
    VmSize:     131168 kB
    VmLck:           0 kB
    VmPin:           0 kB
    VmHWM:       13484 kB
    VmRSS:       13484 kB
    RssAnon:     10264 kB
    RssFile:      3220 kB
    RssShmem:        0 kB
    VmData:      10332 kB
    VmStk:         136 kB
    VmExe:         992 kB
    VmLib:        2104 kB
    VmPTE:          76 kB
    VmPMD:          12 kB
    VmSwap:          0 kB
    HugetlbPages:          0 kB        # 4.4
    CoreDumping:   0                       # 4.15
    Threads:        1
    SigQ:   0/3067
    SigPnd: 0000000000000000
    ShdPnd: 0000000000000000
    SigBlk: 0000000000010000
    SigIgn: 0000000000384004
    SigCgt: 000000004b813efb
    CapInh: 0000000000000000
    CapPrm: 0000000000000000
    CapEff: 0000000000000000
    CapBnd: ffffffffffffffff
    CapAmb:   0000000000000000
    NoNewPrivs:     0
    Seccomp:        0
    Speculation_Store_Bypass:       vulnerable
    Cpus_allowed:   00000001
    Cpus_allowed_list:      0
    Mems_allowed:   1
    Mems_allowed_list:      0
    voluntary_ctxt_switches:        150
    nonvoluntary_ctxt_switches:     545
    """)

    data = parse_proc_human(contents.splitlines())
    assert 13807616 == data["VmRSS"]
