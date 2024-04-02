import { createApp } from "vue";

import Dashboard from "./views/Dashboard.vue";

createApp({
  components: {
    dashboard: Dashboard,
  },
}).mount("#app");
