from os.path import realpath

from temboardui.web import (
    Blueprint,
    TemplateRenderer,
)

blueprint = Blueprint()
render_template = TemplateRenderer(realpath(__file__ + '/../../templates'))
