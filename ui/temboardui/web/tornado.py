import logging

from temboardtoolkit.utils import utcnow
from tornado import web as tornadoweb
from tornado.escape import url_escape
from tornado.web import Application as TornadoApplication

logger = logging.getLogger(__name__)


def serialize_querystring(query):
    return "&".join(
        [
            f"{url_escape(name)}={url_escape(value)}"
            for name, value in sorted(query.items())
        ]
    )


class WebApplication(TornadoApplication):
    def __init__(self, *a, **kwargs):
        super().__init__(*a, **kwargs)

    def configure(self, **settings):
        # Runtime configuration of application.
        #
        # This way, we can initialize app at import time to register handlers.
        # Then configure it at run time once configuration is parsed.

        self.settings.update(settings)

        # This comes from Tornado's __init__
        if self.settings.get("debug"):
            self.settings.setdefault("autoreload", True)
            self.settings.setdefault("compiled_template_cache", False)
            self.settings.setdefault("static_hash_cache", False)
            self.settings.setdefault("serve_traceback", True)

        self.start_time = utcnow()

    def add_rules(self, rules):
        if hasattr(self, "wildcard_router"):  # Tornado 4.5+
            self.wildcard_router.add_rules(rules)
        elif not self.handlers:
            self.add_handlers(r".*$", rules)
        else:
            rules = [tornadoweb.URLSpec(*r) for r in rules]
            self.handlers[0][1].extend(rules)


app = WebApplication()
# Hijack tornado.web access_log to log request in temboardui namespace.
tornadoweb.access_log = logging.getLogger(__package__)
