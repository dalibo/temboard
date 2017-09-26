def test_big_main(mocker):
    pa = mocker.patch('temboardagent.cli.temboardOptions.parse_args')
    pa.return_value = (mocker.Mock(), mocker.Mock())
    mocker.patch('temboardagent.cli.Configuration')
    mocker.patch('temboardagent.cli.daemonize')
    mocker.patch('temboardagent.cli.get_logger')
    mocker.patch('temboardagent.cli.httpd_run')
    mocker.patch('temboardagent.cli.load_plugins_configurations')
    mocker.patch('temboardagent.cli.Process')
    mocker.patch('temboardagent.cli.purge_queue_dir')

    from temboardagent.cli import main

    main()
