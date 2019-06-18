import 'bootstrap';
import $ from 'jquery';
window.jQuery = $; window.$ = $;

$(function() {
  //Loads the correct sidebar on window load,
  //collapses the sidebar on window resize.
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

  // Popover activation
  $(document).ready(function() {
    $(function () {
      $('[data-toggle="popover"]').popover()
    })
    $(function () {
      $('[data-toggle="tooltip"]').tooltip()
    })
  });
});

// Don't let popover sanitize tables in popovers
// https://getbootstrap.com/docs/4.3/getting-started/javascript/#sanitizer
$.fn.popover.Constructor.Default.whiteList.table = [];
$.fn.popover.Constructor.Default.whiteList.tr = [];
$.fn.popover.Constructor.Default.whiteList.td = [];
$.fn.popover.Constructor.Default.whiteList.div = [];
$.fn.popover.Constructor.Default.whiteList.tbody = [];
$.fn.popover.Constructor.Default.whiteList.thead = [];
