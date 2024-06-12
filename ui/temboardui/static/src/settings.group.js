// This script requires a global variable group_king.
import dtbs4 from "datatables.net-bs4";
// Import only bootstrap4 styling. Importing other styles conflicts, producing
// weird result.
import "datatables.net-bs4/css/dataTables.bootstrap4.css";
import dtbuttons from "datatables.net-buttons-dt";
import datatables from "datatables.net-dt";
import Vue from "vue";

import DeleteGroupDialog from "./components/settings/DeleteGroupDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";
import UpdateGroupDialog from "./components/settings/UpdateGroupDialog.vue";

datatables(window, $);
dtbuttons(window, $);
dtbs4(window, $);

window.app = new Vue({
  el: "#vue-app",
  components: {
    "environment-migration-dialog": EnvironmentMigrationDialog,
    "delete-group-dialog": DeleteGroupDialog,
    "update-group-dialog": UpdateGroupDialog,
  },
  created() {
    this.$nextTick(() => {
      var table = $("#tableGroups").DataTable({ stateSave: true });
    });
  },
});
