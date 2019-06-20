import dt from 'datatables.net-bs4';
import css from 'datatables.net-bs4/css/dataTables.bootstrap4.css';
dt(window, $);

$(function() {
  $('#tableNotifications').DataTable({
    order: [[0, 'desc']],
    pageLength: 25
  });
});
