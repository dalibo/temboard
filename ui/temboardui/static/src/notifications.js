import DataTable from "datatables.net-bs4";
import { createApp } from "vue";

createApp({
  created() {
    this.$nextTick(() => {
      new DataTable("#tableNotifications", {
        order: [[0, "desc"]],
        pageLength: 25,
      });
    });
  },
}).mount("#app");
