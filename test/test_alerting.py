def test_preproc():
    from temboardui.plugins.monitoring.alerting import check_specs

    data = dict(
        load1=dict(
            data={'loadavg': [{'load1': 1}]},
            expected=1.0,
        ),
        cpu_core=dict(
            data={'cpu': [{'cpu': 'cpu0', 'time_system': 1, 'time_steal': 1,
                           'time_iowait': 1, 'time_user': 1, 'time_idle': 1}]},
            expected={'cpu0': 80.0},
        ),
        memory_usage=dict(
            data={'memory': [{'mem_total': 10, 'mem_free': 2,
                              'mem_cached': 3}]},
            expected=50.0,
        ),
        swap_usage=dict(
            data={'memory': [{'swap_total': 10, 'swap_used': 5}]},
            expected=50.0,
        ),
        fs_usage_mountpoint=dict(
            data={'filesystems_size': [{'mount_point': '.', 'total': 10,
                  'used': 5}]},
            expected={'.': 50.0},
        ),
        wal_files_archive=dict(
            data={'wal_files': [{'archive_ready': 10}]},
            expected=10,
        ),
        wal_files_total=dict(
            data={'wal_files': [{'total': 10}]},
            expected=10,
        ),
        rollback_db=dict(
            data={'xacts': [{'dbname': 'toto', 'n_rollback': 10}]},
            expected={'toto': 10},
        ),
        hitreadratio_db=dict(
            data={'blocks': [{'dbname': 'toto', 'hitmiss_ratio': 10,
                              'blks_read': 10, 'blks_hit': 10}]},
            expected={'toto': 10},
        ),
        sessions_usage=dict(
            data={'sessions': [{'dbname': 'toto', 'idle_in_xact': 1,
                                'idle_in_xact_aborted': 1, 'no_priv': 1,
                                'idle': 1, 'disabled': 1, 'waiting': 1,
                                'active': 1, 'fastpath': 1}],
                  'max_connections': 20},
            expected=40.0,
        ),
        waiting_sessions_db=dict(
            data={'sessions': [{'dbname': 'toto', 'waiting': 1}]},
            expected={'toto': 1},
        ),
    )

    for k, d in data.items():
        assert d['expected'] == check_specs[k]['preprocess'](d['data'])


def test_bootstrap_checks():
    from temboardui.plugins.monitoring.alerting import bootstrap_checks

    for c in bootstrap_checks({'n_cpu': 1}):
        assert len(c) == 3
        assert c[0] in ['load1', 'cpu_core', 'memory_usage', 'swap_usage',
                        'fs_usage_mountpoint', 'wal_files_archive',
                        'wal_files_total', 'rollback_db', 'hitreadratio_db',
                        'sessions_usage', 'waiting_sessions_db']
        assert type(c[1]) in (int, float)
        assert type(c[2]) in (int, float)


def test_get_highest_state():
    from temboardui.plugins.monitoring.alerting import get_highest_state

    checks = ['OK', 'WARNING', 'CRITICAL']
    assert get_highest_state(checks) == 'CRITICAL'

    checks = ['OK', 'WARNING']
    assert get_highest_state(checks) == 'WARNING'
