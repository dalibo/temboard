import Vue from "vue";

import MaintenanceSchema from "./views/maintenance/Schema.vue";

new Vue({
  el: "#app",
  components: {
    maintenanceschema: MaintenanceSchema,
  },
});
