// This script requires a global variable group_king.
import dtbs4 from "datatables.net-bs4";
// Import only bootstrap4 styling. Importing other styles conflicts, producing
// weird result.
import "datatables.net-bs4/css/dataTables.bootstrap4.css";
import dtbuttons from "datatables.net-buttons-dt";
import datatables from "datatables.net-dt";
import Vue from "vue";

import DeleteUserDialog from "./components/settings/DeleteUserDialog.vue";
import UpdateUserDialog from "./components/settings/UpdateUserDialog.vue";

datatables(window, $);
dtbuttons(window, $);
dtbs4(window, $);

new Vue({
  el: "#app",
  components: {
    "update-user-dialog": UpdateUserDialog,
    "delete-user-dialog": DeleteUserDialog,
  },
  created() {
    this.$nextTick(() => {
      $("#tableUsers").DataTable({ stateSave: true });
    });
  },
});
