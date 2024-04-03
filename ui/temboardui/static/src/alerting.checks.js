import { createApp } from "vue";

import AlertingChecks from "./views/AlertingChecks.vue";

createApp({
  el: "#app",
  components: {
    "alerting-checks": AlertingChecks,
  },
}).mount("#app");
