class FakeResult(object):

    def fetchone(self):
        return ['blabla']


class FakeSession(object):
    def __init__(self):
        self.queries = list()

    def execute(self, query, params):
        self.queries.append((query, params))
        return FakeResult()


def test_get_instance_id():
    from temboardui.plugins.monitoring.tools import get_instance_id
    session = FakeSession()
    get_instance_id(session, 1, 1)
    assert session.queries[0][0] == """
        SELECT instance_id
        FROM monitoring.instances
        WHERE host_id = :host_id AND port = :port
    """
    assert session.queries[0][1] == dict(host_id=1, port=1)


def test_get_host_id():
    from temboardui.plugins.monitoring.tools import get_host_id
    session = FakeSession()
    get_host_id(session, 'toto')
    assert session.queries[0][0] == """
        SELECT host_id FROM monitoring.hosts
        WHERE hostname = :hostname
    """
    assert session.queries[0][1] == dict(hostname='toto')


def test_check_agent_key():
    from temboardui.plugins.monitoring.tools import check_agent_key
    session = FakeSession()
    check_agent_key(session, 'toto', 'plop', 1, 'blabla')
    assert session.queries[0][0] == """
        SELECT agent_key
        FROM application.instances
        WHERE hostname = :hostname AND pg_data=:pgdata AND pg_port = :pgport
        LIMIT 1
    """
    assert session.queries[0][1] == dict(hostname='toto', pgdata='plop',
                                         pgport=1)
