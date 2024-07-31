import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import EditGroupDialog from "./components/EditGroupDialog.vue";
import DeleteGroupDialog from "./components/settings/DeleteGroupDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    "environment-migration-dialog": EnvironmentMigrationDialog,
    "delete-group-dialog": DeleteGroupDialog,
    "edit-group-dialog": EditGroupDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableGroups", {
        stateSave: true,
        autoWidth: false,
        columns: [{ width: "32rem" }, { width: "auto" }, { width: "6rem" }],
      });
    });
  },
}).mount("#vue-app");
