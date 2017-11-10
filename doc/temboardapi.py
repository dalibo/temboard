"""
temBoard API auto-builder

Forked from sphinxcontrib.autohttp.bottle
"""

import re
import six

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList

from sphinx.util import force_decode
from sphinx.util.compat import Directive
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.docstrings import prepare_docstring
from sphinx.pycode import ModuleAnalyzer

from sphinxcontrib import httpdomain
from sphinxcontrib.autohttp.common import http_directive

from temboardagent import routing


def get_routes(plugin):
    for route in routing.get_routes():
        if plugin != 'api' and route['module'] == plugin:
            yield route['http_method'], route['path'], route
        if plugin == 'api' and route['module'] == 'temboardagent.api':
            yield route['http_method'], route['path'], route


class AutotemBoardDirective(Directive):

    has_content = True
    required_arguments = 1
    option_spec = {'endpoints': directives.unchanged,
                   'undoc-endpoints': directives.unchanged,
                   'include-empty-docstring': directives.unchanged}

    @property
    def endpoints(self):
        endpoints = self.options.get('endpoints', None)
        if not endpoints:
            return None
        return frozenset(re.split(r'\s*,\s*', endpoints))

    @property
    def undoc_endpoints(self):
        undoc_endpoints = self.options.get('undoc-endpoints', None)
        if not undoc_endpoints:
            return frozenset()
        return frozenset(re.split(r'\s*,\s*', undoc_endpoints))

    def make_rst(self):
        plugin = self.arguments[0]
        plg = __import__(plugin)
        for method, path, target in get_routes(plugin):
            endpoint = target['function']
            if self.endpoints and endpoint not in self.endpoints:
                continue
            if endpoint in self.undoc_endpoints:
                continue
            view = getattr(plg, target['function'])
            docstring = view.__doc__ or ''
            if not isinstance(docstring, six.text_type):
                analyzer = ModuleAnalyzer.for_module(view.__module__)
                docstring = force_decode(docstring, analyzer.encoding)
            if not docstring and 'include-empty-docstring' not in self.options:
                continue
            docstring = prepare_docstring(docstring)
            for line in http_directive(method, path, docstring):
                yield line

    def run(self):
        node = nodes.section()
        node.document = self.state.document
        result = ViewList()
        for line in self.make_rst():
            result.append(line, '<autotemboard>')
        nested_parse_with_titles(self.state, result, node)
        return node.children


def setup(app):
    if 'sphinxcontrib.httpdomain' not in app.extensions:
        httpdomain.setup(app)
    app.add_directive('autotemboard', AutotemBoardDirective)
