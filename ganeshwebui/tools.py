from tornado.web import HTTPError

GANESHD_SERVERS = [
    {
        'hostname': 'test',
        'host': '127.0.0.2',
        'port': 2346
    },
    {
        'hostname': 'poseidon',
        'host': '127.0.0.1',
        'port': 2345
    }
]

def get_ganeshd_server(p_ganeshd_host, p_ganeshd_port):
    for server in GANESHD_SERVERS:
        if server['host'] == p_ganeshd_host and server['port'] == int(p_ganeshd_port):
            return server
    raise HTTPError(404)
