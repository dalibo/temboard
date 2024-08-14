import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import DeleteDialog from "./components/DeleteDialog.vue";
import UpdateUserDialog from "./components/settings/UpdateUserDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    "update-user-dialog": UpdateUserDialog,
    deletedialog: DeleteDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableUsers", {
        stateSave: true,
        columns: [
          { width: "auto" }, // Username
          { width: "auto" }, // Email
          { width: "12rem" }, // Phone
          { width: "6rem" }, // Active
          { width: "6rem" }, // Admin
          { width: "auto" }, // Groups
          { width: "6rem" }, // Actions
        ],
      });
    });
  },
}).mount("#vueapp");
