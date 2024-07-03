import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import DeleteUserDialog from "./components/settings/DeleteUserDialog.vue";
import UpdateUserDialog from "./components/settings/UpdateUserDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    "update-user-dialog": UpdateUserDialog,
    "delete-user-dialog": DeleteUserDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableUsers", { stateSave: true });
    });
  },
}).mount("#app");
