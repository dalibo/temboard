import './temboard.scss'
// Should not be in common module. Here for legacy.
import hljs from 'highlightjs'

// Export hljs in global namespace.
window.hljs = hljs;

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
});
