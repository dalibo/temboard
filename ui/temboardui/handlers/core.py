from ..web.tornado import (
    app,
    render_template,
)


@app.instance_route('/about')
def home(request):
    return render_template(
        'instance-about.html',
        nav=True,
        instance=request.instance.instance,
        agent_username=request.instance.get_username(),
        role=request.current_user,
    )
