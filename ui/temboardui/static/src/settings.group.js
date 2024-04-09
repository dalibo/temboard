import DataTable from "datatables.net-bs4";
import { createApp } from "vue";

import DeleteGroupDialog from "./components/settings/DeleteGroupDialog.vue";
import EnvironmentMigrationDialog from "./components/settings/EnvironmentMigrationDialog.vue";
import UpdateGroupDialog from "./components/settings/UpdateGroupDialog.vue";

createApp({
  components: {
    "environment-migration-dialog": EnvironmentMigrationDialog,
    "delete-group-dialog": DeleteGroupDialog,
    "update-group-dialog": UpdateGroupDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTable("#tableGroups", { stateSave: true });
    });
  },
}).mount("#vue-app");
