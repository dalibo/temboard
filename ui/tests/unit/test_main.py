def test_pgvar_map():
    from temboardui.cli.app import map_pgvars

    env = dict(
        PGHOST="localhost",
        PGPORT="5433",
        PGUSER="temboard",
        PGPASSWORD="étagère",
        PGDATABASE="temboarddb",
    )
    mapped = map_pgvars(env)
    assert "localhost" == mapped["TEMBOARD_REPOSITORY_HOST"]
    assert "5433" == mapped["TEMBOARD_REPOSITORY_PORT"]
    assert "temboard" == mapped["TEMBOARD_REPOSITORY_USER"]
    assert "étagère" == mapped["TEMBOARD_REPOSITORY_PASSWORD"]
    assert "temboarddb" == mapped["TEMBOARD_REPOSITORY_DBNAME"]

    env = dict(PGHOST="pg", TEMBOARD_REPOSITORY_HOST="temboard")
    mapped = map_pgvars(env)
    assert "temboard" == mapped["TEMBOARD_REPOSITORY_HOST"]
