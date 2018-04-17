def test_preproc():
    from temboardui.plugins.monitoring.alerting import check_specs

    data = dict(
        loadaverage=dict(
            data={'loadavg': [{'load1': 1}]},
            expected=1.0,
        ),
        cpu=dict(
            data={'cpu': [{'cpu': 'cpu0', 'time_system': 1, 'time_steal': 1,
                           'time_iowait': 1, 'time_user': 1, 'time_idle': 1}]},
            expected={'cpu0': 80.0},
        ),
        memory=dict(
            data={'memory': [{'mem_total': 10, 'mem_free': 2,
                              'mem_cached': 3}]},
            expected=50.0,
        ),
        swap=dict(
            data={'memory': [{'swap_total': 10, 'swap_used': 5}]},
            expected=50.0,
        ),
        fs=dict(
            data={'filesystems_size': [{'mount_point': '.', 'total': 10,
                  'used': 5}]},
            expected={'.': 50.0},
        ),
        archive_ready=dict(
            data={'wal_files': [{'archive_ready': 10}]},
            expected=10,
        ),
        wal_files=dict(
            data={'wal_files': [{'total': 10}]},
            expected=10,
        ),
        xacts_rollback=dict(
            data={'xacts': [{'dbname': 'toto', 'n_rollback': 10}]},
            expected={'toto': 10},
        ),
        hitratio=dict(
            data={'blocks': [{'dbname': 'toto', 'hitmiss_ratio': 10,
                              'blks_read': 10, 'blks_hit': 10}]},
            expected={'toto': 10},
        ),
        sessions=dict(
            data={'sessions': [{'dbname': 'toto', 'idle_in_xact': 1,
                                'idle_in_xact_aborted': 1, 'no_priv': 1,
                                'idle': 1, 'disabled': 1, 'waiting': 1,
                                'active': 1, 'fastpath': 1}],
                  'max_connections': 20},
            expected=40.0,
        ),
        waiting=dict(
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
        assert c[0] in ['loadaverage', 'cpu', 'memory', 'swap', 'fs',
                        'archive_ready', 'wal_files', 'xacts_rollback',
                        'hitratio', 'sessions', 'waiting']
        assert type(c[1]) in (int, float)
        assert type(c[2]) in (int, float)
