import Vue from "vue";

import MaintenanceDatabase from "./views/maintenance/Database.vue";

new Vue({
  el: "#app",
  components: {
    maintenancedatabase: MaintenanceDatabase,
  },
});
