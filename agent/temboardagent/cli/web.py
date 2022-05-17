from ..toolkit.app import SubCommand
from .app import app


@app.command
class Web(SubCommand):
    """Standalone web server

    For testing purpose only. Some feature won't work without combined task
    manager processes. See serve command for production.

    """

    def main(self, args):

        self.app.httpd.run()

        return 0
