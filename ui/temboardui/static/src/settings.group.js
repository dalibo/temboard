import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

import DeleteGroupDialog from "./components/settings/DeleteGroupDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";
import UpdateGroupDialog from "./components/settings/UpdateGroupDialog.vue";

DataTable.use(DataTablesLib);

createApp({
  components: {
    "environment-migration-dialog": EnvironmentMigrationDialog,
    "delete-group-dialog": DeleteGroupDialog,
    "update-group-dialog": UpdateGroupDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableGroups", { stateSave: true });
    });
  },
}).mount("#vue-app");
