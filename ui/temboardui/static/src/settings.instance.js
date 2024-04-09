import DataTable from "datatables.net-bs4";
import "datatables.net-buttons-bs4";
import { createApp } from "vue";

import DeleteInstanceDialog from "./components/settings/DeleteInstanceDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";
import NewInstanceWizard from "./components/settings/NewInstanceWizard.vue";
import UpdateInstanceDialog from "./components/settings/UpdateInstanceDialog.vue";

createApp({
  components: {
    "delete-instance-dialog": DeleteInstanceDialog,
    "environment-migration-dialog": EnvironmentMigrationDialog,
    "new-instance-wizard": NewInstanceWizard,
    "update-instance-dialog": UpdateInstanceDialog,
  },
  created() {
    this.$nextTick(() => {
      const table = new DataTable("#tableInstances", {
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
              const filter = $(".dt-search input", table.table().container()).val();
              const url = new URLSearchParams({ filter });
              window.location.replace("/settings/instances.csv?" + url.toString());
            },
          },
        ],
        stateSave: true,
      });

      table.buttons().container().appendTo($(".dt-search", table.table().container()));
    });
  },
}).mount("#vue-app");
