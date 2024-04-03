import { createApp } from "vue";

import MaintenanceTable from "./views/maintenance/Table.vue";

createApp({
  el: "#app",
  components: {
    maintenancetable: MaintenanceTable,
  },
}).mount("#app");
