import dt from 'datatables.net-bs4';
dt(window, $);

$(function() {
  $('#tableNotifications').DataTable({
    order: [[0, 'desc']],
    pageLength: 25
  });
});
