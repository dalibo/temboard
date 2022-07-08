import logging

from ..toolkit.app import SubCommand
from .app import app


logger = logging.getLogger(__name__)


@app.command
class RunScript(SubCommand):
    """ Run a Python script. """

    def define_arguments(self, parser):
        parser.add_argument(
            'script', metavar='PATH',
            help="Path to script file.",
        )

        super(RunScript, self).define_arguments(parser)

    def main(self, args):
        with open(args.script) as fo:
            source = fo.read()
        code = compile(source, args.script, 'exec')

        g = globals()
        g['app'] = self.app

        exec(code, g, g)
