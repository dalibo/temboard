import os.path
import logging
from urllib.parse import urlparse

from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..toolkit.http import TemboardClient
from ..toolkit.signing import load_public_key
from .app import app


logger = logging.getLogger(__name__)


@app.command
class FetchKey(SubCommand):
    """Fetch signing public key."""

    name = 'fetch-key'

    def define_arguments(self, parser):
        parser.add_argument(
            "--force",
            action='store_true', default=False,
            help="Force overwriting existing files.",
        )

    def main(self, args):
        pub = self.app.config.temboard.signing_public_key
        if os.path.exists(pub) and not args.force:
            raise UserError("%s exists. Use --force to overwrite." % pub)

        ui_url_raw = self.app.config.temboard.ui_url.rstrip('/')
        ui_url = urlparse(ui_url_raw)
        ui_client = TemboardClient.factory(
            self.app.config,
            scheme=ui_url.scheme, host=ui_url.hostname, port=ui_url.port,
        )

        logger.info("Requesting public key from %s.", ui_url_raw)
        response = ui_client.get('/signing.key')
        response.raise_for_status()
        pem = response.read()

        logger.info("Validating PEM data.")
        load_public_key(pem)

        with open(pub, 'wb') as fo:
            fo.write(pem)

        logger.info("%s updated from %s.", pub, ui_url_raw)
        logger.info("Please reload agent service if running.")

        return 0
