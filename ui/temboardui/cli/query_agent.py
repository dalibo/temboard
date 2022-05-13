import logging
import sys

from ..temboardclient import TemboardAgentClient
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..toolkit.pycompat import urlparse
from ..toolkit import validators as v
from .app import app


logger = logging.getLogger(__name__)


@app.command
class QueryAgent(SubCommand):
    """Query a temBoard agent

    Accepts body contents in stdin. temBoard agent accepts only JSON as body.

    """

    name = 'query-agent'

    def define_arguments(self, parser):
        parser.add_argument(
            'url', metavar='URL',
            help="Full URL to agent to query.",
            type=v.url,
        )

        parser.add_argument(
            'body', default=None, nargs='?', metavar='JSON',
            help="JSON payload for POST request.",
        )

        super(QueryAgent, self).define_arguments(parser)

    def main(self, args):
        url = urlparse(args.url)

        if not args.body and not sys.stdin.isatty():
            logger.info("Reading request body from STDIN.")
            args.body = sys.stdin.read()

        method = 'POST' if args.body else 'GET'
        pathinfo = url.path
        if url.query:
            pathinfo = "%s?%s" % (pathinfo, url.query)

        client = TemboardAgentClient.factory(
            self.app.config, url.hostname, url.port,
        )

        try:
            response = client.request(method, pathinfo, body=args.body)
            response.raise_for_status()
        except client.ConnectionError as e:
            logger.critical("%s", e)
            return 1
        except client.Error as e:
            self.print_headers(response)
            raise UserError(str(e))
        else:
            self.print_headers(response)
            sys.stdout.write(response.read().decode('utf-8'))

        return 0

    def print_headers(self, response):
        for name, value in sorted(response.headers.items()):
            sys.stderr.write("%s: %s\n" % (name, value))
