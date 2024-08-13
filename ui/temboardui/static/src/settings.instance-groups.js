import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import DeleteDialog from "./components/DeleteDialog.vue";
import EditGroupDialog from "./components/EditGroupDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    "environment-migration-dialog": EnvironmentMigrationDialog,
    deletedialog: DeleteDialog,
    "edit-group-dialog": EditGroupDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableGroups", {
        stateSave: true,
        autoWidth: false,
        columns: [{ width: "32rem" }, { width: "auto" }, { width: "auto" }, { width: "6rem" }],
      });
    });
  },
}).mount("#vue-app");
