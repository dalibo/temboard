import './temboard.scss'
import 'font-awesome/css/font-awesome.css'

$(() => {
  // Mark active link in sidebar
  var url = window.location;
  var element = $('ul.nav a').filter(function() {
    return this.href == url || url.href.indexOf(this.href) == 0;
  }).addClass('active').parent().parent().addClass('in').parent();

  if (element.is('li')) {
    element.addClass('active');
  }

  // Sidebar collapsology
  if (eval(localStorage.getItem('sidebarCollapsed'))) {
    document.body.className += 'sidebar-collapsed';
  }

  $('#menu-collapse').click(function(event) {
    event.preventDefault();
    $(document.body).toggleClass('sidebar-collapsed');
    localStorage.setItem('sidebarCollapsed', $(document.body).hasClass('sidebar-collapsed'));
    window.dispatchEvent(new Event('resize'));
  });

  // Popover and tooltip initialization
  $('[data-toggle="popover"]').popover()
  $('[data-toggle="tooltip"]').tooltip()
});
