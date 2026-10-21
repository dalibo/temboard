from datetime import datetime, timedelta


# Stolen from ldap2pg
class Stopwatch:
    def __init__(self):
        self.delta = timedelta()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.delta}>"

    def __enter__(self):
        self.start = datetime.utcnow()

    def __exit__(self, *_):
        self.last_delta = datetime.utcnow() - self.start
        self.delta += self.last_delta
        self.start = None
