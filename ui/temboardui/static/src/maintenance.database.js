import { createApp } from "vue";

import MaintenanceDatabase from "./views/maintenance/Database.vue";

createApp({
  components: {
    maintenancedatabase: MaintenanceDatabase,
  },
}).mount("#app");
