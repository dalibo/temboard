class Status(object):
    def __init__(self, app):
        self.app = app
        self.data = dict(
            postgres=dict(available=True),
            temboard=dict(),
            system=dict(),
        )
