from ...web.flask import instance_proxy


class DashboardPlugin:
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        __import__(__name__ + ".routes")
        instance_proxy.generic_proxy("/dashboard")
