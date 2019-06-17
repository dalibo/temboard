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
