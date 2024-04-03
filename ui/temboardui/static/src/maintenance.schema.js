import { createApp } from "vue";

import MaintenanceSchema from "./views/maintenance/Schema.vue";

createApp({
  el: "#app",
  components: {
    maintenanceschema: MaintenanceSchema,
  },
}).mount("#app");
