// This script requires a global variable group_king.
import Vue from "vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";

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
  components: {
    "environment-migration-dialog": EnvironmentMigrationDialog,
  },
  created() {
    this.$nextTick(() => {
      var table = $("#tableGroups").DataTable({ stateSave: true });

      $("#buttonLoadAddGroupForm").click(function () {
        $("#GroupModal").modal("show");
        $("[data-toggle=popover]").popover("hide");
        load_add_group_form("GroupModal", group_kind);
      });

      $(document).on("click", "[data-action=edit]", function () {
        $("#GroupModal").modal("show");
        $("[data-toggle=popover]").popover("hide");
        load_update_group_form("GroupModal", group_kind, $(this).data("group_name"));
      });

      $(document).on("click", "[data-action=delete]", function () {
        $("#GroupModal").modal("show");
        $("[data-toggle=popover]").popover("hide");
        load_delete_group_confirm("GroupModal", group_kind, $(this).data("group_name"));
      });
    });
  },
});
