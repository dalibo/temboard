def pg_version(conn):
    """
    Returns the PostgreSQL server version as numeric and full version.
    """
    num_version = conn.get_pg_version()
    conn.execute("SELECT version()")
    full_version = list(conn.get_rows())[0]['version']
    return dict(numeric=num_version, full=full_version)
