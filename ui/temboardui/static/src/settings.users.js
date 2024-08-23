import DataTablesLib from "datatables.net-bs5";
import "datatables.net-buttons-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import DeleteDialog from "./components/DeleteDialog.vue";
import EditUserDialog from "./components/settings/EditUserDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    edituserdialog: EditUserDialog,
    deletedialog: DeleteDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableUsers", {
        pageLength: 50,
        stateSave: true,
        columns: [
          { width: "auto" }, // Username
          { width: "auto" }, // Email
          { width: "12rem" }, // Phone
          { width: "6rem" }, // Active
          { width: "6rem" }, // Admin
          { width: "auto" }, // Groups
          { width: "6rem", orderable: false }, // Actions
        ],
        layout: {
          topStart: "search",
          topEnd: {
            buttons: [
              {
                text: "New user",
                className: "btn btn-sm btn-success",
                attr: {
                  id: "buttonNewUser",
                  "data-bs-toggle": "modal",
                  "data-bs-target": "#modalEditUser",
                },
              },
            ],
          },
        },
      });
    });
  },
}).mount("#vueapp");
