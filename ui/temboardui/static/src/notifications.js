import DataTablesLib from "datatables.net-bs5";
import DataTable from "datatables.net-vue3";
import { createApp } from "vue";

DataTable.use(DataTablesLib);

createApp({
  created() {
    this.$nextTick(() => {
      new DataTablesLib("#tableNotifications", {
        order: [[0, "desc"]],
        pageLength: 25,
      });
    });
  },
}).mount("#app");
