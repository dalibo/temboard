import logging
import ssl
from socket import error as SocketError
from wsgiref.simple_server import ServerHandler, WSGIRequestHandler, make_server

from bottle import debug, default_app

from .. import __version__
from ..errors import UserError
from ..toolkit import syncio

logger = logging.getLogger(__package__)


class HTTPDService(syncio.Service):
    name = "web"

    def __init__(self, app):
        self.app = app

    def __str__(self):
        return self.name

    # for services.run
    def setup(self, *_, **__):
        ServerHandler.server_software = "temBoard-agent/%s" % __version__

        try:
            bottle = default_app()
            debug(self.app.debug)

            self.server = make_server(
                self.app.config.temboard.address,
                self.app.config.temboard.port,
                app=bottle,
                handler_class=CustomWSGIRequestHandler,
            )
        except SocketError as e:
            raise UserError(f"Failed to start HTTPS server: {e}.")
        try:
            logger.debug("Using SSL key %s.", self.app.config.temboard.ssl_key_file)
            logger.debug(
                "Using SSL certificate %s.", self.app.config.temboard.ssl_cert_file
            )
            ctx = ssl.SSLContext()
            ctx.load_cert_chain(
                self.app.config.temboard.ssl_cert_file,
                self.app.config.temboard.ssl_key_file,
            )
            ctx.set_ciphers(
                ":".join(
                    [
                        # From Mozilla SSL configuration generator. 2023-07-28
                        "ECDHE-ECDSA-AES128-GCM-SHA256",
                        "ECDHE-RSA-AES128-GCM-SHA256",
                        "ECDHE-ECDSA-AES256-GCM-SHA384",
                        "ECDHE-RSA-AES256-GCM-SHA384",
                        "ECDHE-ECDSA-CHACHA20-POLY1305",
                        "ECDHE-RSA-CHACHA20-POLY1305",
                        "DHE-RSA-AES128-GCM-SHA256",
                        "DHE-RSA-AES256-GCM-SHA384",
                        "DHE-RSA-CHACHA20-POLY1305",
                    ]
                )
            )

            self.server.socket = ctx.wrap_socket(self.server.socket, server_side=True)
        except Exception as e:
            raise UserError(f"Failed to setup SSL: {e}.")
        self.server.timeout = 1

        logger.info(
            "Serving at https://%s:%s.",
            self.app.config.temboard.address,
            self.app.config.temboard.port,
        )

    # for syncio.Loop
    def accept(self):
        self.server.handle_request()


class CustomWSGIRequestHandler(WSGIRequestHandler):
    def get_environ(self):
        env = super().get_environ()

        # Save raw PATH_INFO for signature computation.
        path, _, _ = self.path.partition("?")
        env["RAW_PATH_INFO"] = path

        return env

    def log_request(self, code="-", size="-"):
        if code > "50":
            logmethod = logger.error
        else:
            logmethod = logger.info
        logmethod(
            # Same format as Tornado access.
            "%s %s %s (%s) %s %s",
            code,
            self.command,  # Method
            self.path,
            self.address_string(),
            "-",  # Not timed.
            size,
        )
