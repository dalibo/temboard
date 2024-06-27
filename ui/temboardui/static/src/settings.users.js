import DataTable from "datatables.net-bs4";
import { createApp } from "vue";

import DeleteUserDialog from "./components/settings/DeleteUserDialog.vue";
import UpdateUserDialog from "./components/settings/UpdateUserDialog.vue";

createApp({
  components: {
    "update-user-dialog": UpdateUserDialog,
    "delete-user-dialog": DeleteUserDialog,
  },
  created() {
    this.$nextTick(() => {
      new DataTable("#tableUsers", { stateSave: true });
    });
  },
}).mount("#app");
