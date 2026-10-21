from textwrap import dedent

from .model.orm import CollectorStatus, Host, Instance


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


def merge_agent_info(session, host_info, instance_info):
    """Update the host, instance and database information with the
    data received from the agent."""

    try:
        # Try to get host_id, based on hostname
        host_info["host_id"] = get_host_id(session, host_info["hostname"])
    except NameError:
        # host not found
        pass

    host = Host.from_dict(host_info)

    # Insert or update host information
    session.merge(host)
    session.flush()
    session.commit()

    # Get host_id in any case
    host_id = get_host_id(session, host_info["hostname"])
    # Weird that SA does not update this.
    host.host_id = host_id

    # Only process instances marked as available, since only those
    # have complete information
    if instance_info["available"]:
        try:
            # Try to get instance_id
            instance_info["instance_id"] = get_instance_id(
                session, host_id, instance_info["port"]
            )
        except Exception:
            # instance not found
            pass
        instance_info["host_id"] = host_id

        inst = Instance.from_dict(instance_info)
        # Insert or update instance information
        session.merge(inst)
        session.flush()
        session.commit()
    return host


def update_collector_status(
    session, instance_id, status, last_pull=None, last_push=None, last_insert=None
):
    cs = CollectorStatus()
    cs.instance_id = instance_id
    cs.status = status
    if last_pull:
        cs.last_pull = last_pull
    if last_push:
        cs.last_push = last_push
    if last_insert:
        cs.last_insert = last_insert

    session.merge(cs)
