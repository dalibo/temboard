import os.path
import logging
from subprocess import check_call

from cryptography.hazmat.primitives import serialization

from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..toolkit.signing import load_private_key
from .app import app


logger = logging.getLogger(__name__)


@app.command
class GenerateKey(SubCommand):
    """Generate signing key."""

    name = 'generate-key'

    def define_arguments(self, parser):
        parser.add_argument(
            "--force",
            action='store_true', default=False,
            help="Force overwriting existing files.",
        )

    def main(self, args):
        priv = self.app.config.temboard.signing_private_key
        if os.path.exists(priv) and not args.force:
            raise UserError("%s exists. Use --force to overwrite." % priv)
        logger.info("Generating RSA key with openssl at %s.", priv)
        check_call(['openssl', 'genrsa', '-out', priv, '4096'])

        with open(priv, 'rb') as fo:
            privkey = load_private_key(fo.read())

        pub = self.app.config.temboard.signing_public_key
        logger.info("Exporting public key at %s.", pub)
        pem = privkey.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        with open(pub, 'wb') as fo:
            fo.write(pem)

        return 0
