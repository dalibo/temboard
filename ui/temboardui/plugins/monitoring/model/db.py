from textwrap import dedent


def get_host_id(session, hostname):
    row = session.execute(
        "SELECT host_id FROM monitoring.hosts WHERE hostname = :hostname",
        dict(hostname=hostname),
    ).fetchone()
    if not row:
        raise NameError("Could not find registered host with hostname=%s" % hostname)
    return row[0]


def get_instance_id(session, host_id, port):
    row = session.execute(
        dedent("""
            SELECT instance_id
            FROM monitoring.instances
            WHERE host_id = :host_id AND port = :port
        """),
        dict(host_id=host_id, port=port),
    ).fetchone()
    if not row:
        raise Exception(
            "Could not find registered instance with host_id=%s and port=%s"
            % (host_id, port)
        )
    return row[0]
