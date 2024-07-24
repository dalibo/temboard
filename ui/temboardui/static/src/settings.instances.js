import DataTablesLib from "datatables.net-bs5";
import "datatables.net-buttons-bs5";
import DataTable from "datatables.net-vue3";
import $ from "jquery";
import { createApp } from "vue";

import DeleteDialog from "./components/DeleteDialog.vue";
import InstanceDetails from "./components/settings/InstanceDetails.vue";
import NewInstanceWizard from "./components/settings/NewInstanceWizard.vue";
import UpdateInstanceDialog from "./components/settings/UpdateInstanceDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    "new-instance-wizard": NewInstanceWizard,
    "update-instance-dialog": UpdateInstanceDialog,
    deletedialog: DeleteDialog,
    instancedetails: InstanceDetails,
  },
  created() {
    this.$nextTick(() => {
      const table = new DataTablesLib("#tableInstances", {
        pageLength: 50,
        stateSave: true,
        columns: [
          { width: "auto" }, // server
          { width: "auto" }, // postgresql
          { width: "auto" }, // agent
          { width: "6rem" }, // notify
          { width: "6rem", orderable: false }, // actions
        ],
        layout: {
          topStart: "search",
          topEnd: [
            {
              buttons: [
                {
                  attr: {
                    title: "Download inventory as CSV",
                    id: "buttonDownload",
                    "data-bs-toggle": "tooltip",
                  },
                  className: "btn btn-sm btn-secondary",
                  text: `<i class="fa fa-download"></i>`,
                  action: function () {
                    /**
                     * Use temBoard UI API instead of datatable export. UI export includes
                     * more data and has reordered column.
                     */
                    const filter = $(".dt-search input", table.table().container()).val();
                    const url = new URLSearchParams({ filter });
                    window.location.replace("/instances.csv?" + url.toString());
                  },
                },
              ],
            },
            {
              buttons: [
                {
                  text: "New instance",
                  className: "btn btn-sm btn-success ms-1",
                  attr: {
                    id: "buttonNewInstance",
                    "data-bs-toggle": "modal",
                    "data-bs-target": "#modalNewInstance",
                  },
                },
              ],
            },
          ],
        },
      });
    });
  },
}).mount("#vue-app");
