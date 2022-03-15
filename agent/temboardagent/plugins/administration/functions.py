def pg_version(conn):
    """
    Returns the PostgreSQL server version as numeric and full version.
    """
    num_version = conn.server_version
    full_version = conn.query_scalar("SELECT version()")
    return dict(numeric=num_version, full=full_version)
