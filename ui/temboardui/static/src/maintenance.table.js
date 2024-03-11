import Vue from "vue";

import MaintenanceTable from "./views/maintenance/Table.vue";

new Vue({
  el: "#app",
  components: {
    maintenancetable: MaintenanceTable,
  },
});
