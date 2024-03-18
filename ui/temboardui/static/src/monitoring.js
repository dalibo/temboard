import Vue from "vue";
import VueRouter from "vue-router";

import Monitoring from "./views/Monitoring.vue";

const router = new VueRouter();

Vue.use(VueRouter);

new Vue({
  el: "#app",
  components: {
    monitoring: Monitoring,
  },
  router,
});
