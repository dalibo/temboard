import dtbs4 from "datatables.net-bs4";
// Import only bootstrap4 styling. Importing other styles conflicts, producing
// weird result.
import "datatables.net-bs4/css/dataTables.bootstrap4.css";
import dtbuttons from "datatables.net-buttons-dt";
import datatables from "datatables.net-dt";
import Vue from "vue";

import DeleteInstanceDialog from "./components/settings/DeleteInstanceDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";
import NewInstanceWizard from "./components/settings/NewInstanceWizard.vue";
import UpdateInstanceDialog from "./components/settings/UpdateInstanceDialog.vue";

datatables(window, $);
dtbuttons(window, $);
dtbs4(window, $);

window.app = new Vue({
  el: "#vue-app",
  components: {
    "delete-instance-dialog": DeleteInstanceDialog,
    "environment-migration-dialog": EnvironmentMigrationDialog,
    "new-instance-wizard": NewInstanceWizard,
    "update-instance-dialog": UpdateInstanceDialog,
  },
  created() {
    this.$nextTick(() => {
      var table = $("#tableInstances").DataTable({
        lengthChange: false,
        pageLength: 50,
        buttons: [
          {
            attr: {
              title: "Download inventory as CSV",
              id: "buttonDownload",
              "data-toggle": "tooltip",
            },
            className: "btn btn-sm btn-secondary mx-1",
            text: `<i class="fa fa-download"></i>`,
            action: function () {
              /**
               * Use temBoard UI API instead of datatable export. UI export includes
               * more data and has reordered column.
               */
              var filter = $("#tableInstances_filter input").val();
              var url = new URLSearchParams({ filter });
              window.location.replace("/settings/instances.csv?" + url.toString());
            },
          },
        ],
        stateSave: true,
      });

      table.buttons().container().appendTo($("#tableInstances_filter"));
    });
  },
});
