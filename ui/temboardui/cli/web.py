from ..model import check_schema
from ..toolkit.app import SubCommand
from .app import app


@app.command
class web(SubCommand):
    """Standalone web server.

    For testing purpose only. Some feature won't work without combined task
    manager processes. See serve command for production.

    """

    def main(self, args):
        check_schema()
        self.app.config.load_signing_key()
        self.app.webservice.run()
