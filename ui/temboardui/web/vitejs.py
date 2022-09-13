# Integration of ViteJS in temBoard
import json
import logging
import os


logger = logging.getLogger(__name__)


class ViteJSExtension(object):
    # Flask extension managing ViteJS

    def __init__(self, app=None):
        self.app = app
        self.manifest = None
        if app:
            self.init_app(app)

    @property
    def PROD(self):
        return not bool(self.app.config.get('VITEJS'))

    def init_app(self, app):
        app.vitejs = self
        app.config['VITEJS'] = uri = os.environ.get('VITEJS', '').rstrip('/')
        if uri and not uri.startswith('http://localhost:'):
            raise Exception("Refusing to delegate to non-localhost ViteJS.")
        self.manifest_path = self.app.static_folder + '/manifest.json'

    def read_manifest(self):
        if self.app.config['VITEJS']:
            logger.debug(
                "Using ViteJS dev server at %s.", self.app.config['VITEJS'])
            logger.debug("Skip reading ViteJS manifest.")
            return

        logger.debug("Loading ViteJS manifest.")
        with open(self.manifest_path) as fo:
            self.manifest = json.load(fo)

    def url_for(self, name):
        if self.manifest:
            return self.app.static_url_path + '/' + self.manifest[name]['file']
        else:
            return self.app.config['VITEJS'] + '/static/' + name
