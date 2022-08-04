from os.path import realpath

from ....web.tornado import (
    Blueprint,
    TemplateRenderer,
)

blueprint = Blueprint()
render_template = TemplateRenderer(realpath(__file__ + '/../../templates'))
