# Integration of ViteJS in temBoard
import json
import logging


logger = logging.getLogger(__name__)


class ViteJSExtension(object):
    # Flask extension managing ViteJS

    def __init__(self, app=None):
        self.app = app
        self.manifest = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.vitejs = self

    def read_manifest(self):
        logger.debug("Loading ViteJS manifest.")
        path = self.app.static_folder + '/manifest.json'
        with open(path) as fo:
            self.manifest = json.load(fo)

    def url_for(self, name):
        if self.manifest:
            return self.app.static_url_path + '/' + self.manifest[name]['file']
