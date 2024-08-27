from ...web.flask import instance_proxy


class PGConfPlugin:
    def __init__(self, app):
        self.app = app

    def load(self):
        __import__(__name__ + ".routes")
        instance_proxy.generic_proxy("/pgconf/configuration")
        instance_proxy.generic_proxy("/pgconf/configuration", method="POST")
        instance_proxy.generic_proxy("/pgconf/configuration/categories")
        instance_proxy.generic_proxy("/pgconf/configuration/status")
        instance_proxy.generic_proxy("/pgconf/configuration/category/<path:category>")
