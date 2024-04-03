import { createApp } from "vue";

import MaintenanceIndex from "./views/maintenance/Index.vue";

createApp({
  components: {
    maintenanceindex: MaintenanceIndex,
  },
}).mount("#app");
