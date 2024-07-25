import logging

from temboardui.application import check_group_description, check_group_name
from temboardui.web.tornado import HTTPError, admin_required, app, render_template

from ...model import orm

logger = logging.getLogger(__name__)
PREFIX = r"/json/settings"


@app.route("/json/groups")
@admin_required
def get_groups(request):
    groups = request.db_session.execute(orm.Group.all())
    return {
        "groups": [
            {"name": group.name, "description": group.description} for group in groups
        ],
        "loaded_plugins": request.config.temboard.plugins,
    }


@app.route("/json/group/([0-9a-z\-_\.]{3,16})$", methods=["GET", "POST"])
@admin_required
def group(request, name):
    if "GET" == request.method:
        if not name:
            raise HTTPError(404)
        group = request.db_session.execute(orm.Group.get(name)).fetchone()
        return group.asdict()
    else:  # POST
        data = request.json
        if not data.get("new_group_name"):
            raise HTTPError(400, "Missing group name.")
        check_group_name(data["new_group_name"])
        if not data.get("description"):
            raise HTTPError(400, "Missing description")
        check_group_description(data["description"])

        if name:  # Group update
            group = get_group(request.db_session, name, kind)
            if "instance" == kind:
                for ari in group.ari:
                    delete_role_group_from_instance_group(
                        request.db_session, ari.role_group_name, group.group_name
                    )

            group = update_group(
                request.db_session,
                group.group_name,
                kind,
                data["new_group_name"],
                data["description"],
            )
        else:  # Group creation
            group = add_group(
                request.db_session, data["new_group_name"], data["description"], kind
            )

        if "user_groups" in data and data["user_groups"]:
            for group_name in data["user_groups"]:
                add_role_group_in_instance_group(
                    request.db_session, group_name, group.group_name
                )

        return {"ok": True}


@app.route(PREFIX + r"/delete/group/(role|instance)", methods=["POST"])
@admin_required
def delete_group_handler(request, kind):
    name = request.json.get("group_name")
    if not name:
        raise HTTPError(400)
    delete_group(request.db_session, name, kind)
    return {"delete": True}


@app.route(r"/settings/groups/(role|instance)")
@admin_required
def groups(request, kind):
    return render_template(
        "settings/group.html",
        nav=True,
        role=request.current_user,
        group_kind=kind,
        group_list=get_group_list(request.db_session, kind),
    )
