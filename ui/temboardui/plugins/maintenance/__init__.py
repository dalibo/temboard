from ...web.flask import instance_proxy


class MaintenancePlugin:
    def __init__(self, app):
        self.app = app

    def load(self):
        __import__(__name__ + ".routes")
        instance_proxy.generic_proxy("/maintenance")
        instance_proxy.generic_proxy("/maintenance/<database>")
        instance_proxy.generic_proxy("/maintenance/<database>", method="POST")
        instance_proxy.generic_proxy(
            "/maintenance/<any(vacuum,analyze,reindex):action>/<database>",
            method="DELETE",
        )
        instance_proxy.generic_proxy(
            "/maintenance/<database>/<any(vacuum,analyze,reindex):action>",
            method="POST",
        )
        instance_proxy.generic_proxy(
            "/maintenance/<database>/<any(vacuum,analyze,reindex):action>/scheduled"
        )
        instance_proxy.generic_proxy("/maintenance/<database>/schema/<schema>")
        instance_proxy.generic_proxy(
            "/maintenance/<database>/schema/<schema>/<any(vacuum,analyze,reindex):action>/scheduled"
        )
        instance_proxy.generic_proxy(
            "/maintenance/<database>/schema/<schema>/table/<table>"
        )
        instance_proxy.generic_proxy(
            "/maintenance/<database>/schema/<schema>/<any(index,table):type>/<object>/reindex",
            method="POST",
        )
        instance_proxy.generic_proxy(
            "/maintenance/<database>/schema/<schema>/table/<table>/<any(vacuum,analyze):action>",
            method="POST",
        )
        instance_proxy.generic_proxy(
            "/maintenance/<database>/schema/<schema>/table/<table>/<any(vacuum,analyze):action>/scheduled"
        )
