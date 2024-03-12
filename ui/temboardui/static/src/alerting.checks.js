import Vue from "vue";

import AlertingChecks from "./views/AlertingChecks.vue";

new Vue({
  el: "#app",
  components: {
    "alerting-checks": AlertingChecks,
  },
});
