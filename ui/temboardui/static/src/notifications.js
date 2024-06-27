// This script requires a global variable group_king.
import dtbs4 from "datatables.net-bs4";
// Import only bootstrap4 styling. Importing other styles conflicts, producing
// weird result.
import "datatables.net-bs4/css/dataTables.bootstrap4.css";
import dtbuttons from "datatables.net-buttons-dt";
import datatables from "datatables.net-dt";
import Vue from "vue";

datatables(window, $);
dtbuttons(window, $);
dtbs4(window, $);

new Vue({
  el: "#app",
  created() {
    this.$nextTick(() => {
      $("#tableNotifications").DataTable({
        order: [[0, "desc"]],
        pageLength: 25,
      });
    });
  },
});
