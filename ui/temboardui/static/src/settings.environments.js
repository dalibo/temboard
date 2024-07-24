import { Tooltip } from "bootstrap";
import DataTablesLib from "datatables.net-bs5";
import "datatables.net-buttons-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import DeleteDialog from "./components/DeleteDialog.vue";
import EnvironmentDialog from "./components/EnvironmentDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    deletedialog: DeleteDialog,
    environmentdialog: EnvironmentDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableEnvironments", {
        stateSave: true,
        autoWidth: false,
        // name, description, actions
        columns: [{ width: "32rem" }, { width: "auto" }, { width: "8rem", orderable: false }],
        layout: {
          topStart: "search",
          topEnd: {
            buttons: [
              {
                text: "New environment",
                className: "btn btn-sm btn-success",
                attr: {
                  "data-bs-toggle": "modal",
                  "data-bs-target": "#modalEditEnvironment",
                  "data-testid": "new",
                },
              },
            ],
          },
        },
      });

      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => new Tooltip(el));
    });
  },
}).mount("#vue-app");
