import json
import logging
import pprint

from monitoring.probes import Probe
from temboardagent.httpsclient import https_request


class OutputEncoder(json.JSONEncoder):
    """Tell json that probe objects should be encoded as strings using their
    name.
    """
    def default(self, obj):
        if isinstance(obj, Probe):
            return repr(obj)
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def send_output(ca_cert_file, url, key, j_output):
    """Send data to the target URL."""

    logging.debug("Sending output to %s", url)
    logging.debug("Output is:" + pprint.pformat(j_output))
    (code, res, _) = https_request(
        ca_cert_file,
        method='POST',
        url=url,
        headers={
            "Content-type": "application/json",
            "X-Key": key
        },
        data=json.loads(j_output)
    )
    logging.debug("Server replied with status %s", code)


def remove_passwords(instances):
    clean_instances = []
    for instance in instances:
        clean_instance = {}
        for k in instance.keys():
            if k != 'password':
                clean_instance[k] = instance[k]
        clean_instances.append(clean_instance)
    return clean_instances
