from ..web.tornado import (
    app,
    render_template,
)


@app.instance_route('/about')
def home(request):
    request.instance.fetch_status()
    return render_template(
        'instance-about.html',
        nav=True,
        instance=request.instance,
        role=request.current_user,
    )
