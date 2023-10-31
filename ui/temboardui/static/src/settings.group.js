import Vue from "vue";

import datatables from "datatables.net-dt";
import dtbuttons from "datatables.net-buttons-dt";
import dtbs4 from "datatables.net-bs4";
// Import only bootstrap4 styling. Importing other styles conflicts, producing
// weird result.
import "datatables.net-bs4/css/dataTables.bootstrap4.css";

datatables(window, $);
dtbuttons(window, $);
dtbs4(window, $);

window.app = new Vue({
  el: "#vue-app",
  created() {
    this.$nextTick(() => {
      var table = $("#tableGroups").DataTable({ stateSave: true });
    });
  },
});
