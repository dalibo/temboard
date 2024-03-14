import Vue from "vue";
import VueRouter from "vue-router";

import "./daterangepicker.vue.js";
import AlertingCheck from "./views/AlertingCheck.vue";

const router = new VueRouter();

Vue.use(VueRouter);

new Vue({
  el: "#app",
  components: {
    alertingCheck: AlertingCheck,
  },
  router,
});
