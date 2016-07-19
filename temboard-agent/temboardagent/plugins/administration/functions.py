from temboardagent.command import exec_command

def pg_version(conn, config, _):
    num_version = conn.get_pg_version()
    conn.execute("SELECT version()")
    full_version = list(conn.get_rows())[0]['version']
    return {'numeric': num_version, 'full': full_version}
