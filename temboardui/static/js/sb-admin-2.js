//Loads the correct sidebar on window load,
//collapses the sidebar on window resize.
$(function() {
    /*
	$(window).bind("load resize", function() {
        width = (this.window.innerWidth > 0) ? this.window.innerWidth : this.screen.width;
        if (width < 768) {
            $('div.navbar-collapse').addClass('collapse');
        } else {
            $('div.navbar-collapse').removeClass('collapse');
        }
    });
	*/
    var url = window.location;
    var element = $('ul.nav a').filter(function() {
        return this.href == url || url.href.indexOf(this.href) == 0;
    }).addClass('active').parent().parent().addClass('in').parent();
    if (element.is('li')) {
        element.addClass('active');
    }

    $('#menu-collapse').click(function(event) {
      $(document.body).toggleClass('sidebar-collapsed');
      localStorage.setItem('sidebarCollapsed', $(document.body).hasClass('sidebar-collapsed'));
      event.preventDefault();
      window.dispatchEvent(new Event('resize'));
    });
});
