import Vue from "vue";
import AlertingCheck from "./views/AlertingCheck.vue";
import VueRouter from "vue-router";
import "./daterangepicker.vue.js";

const router = new VueRouter();

Vue.use(VueRouter);

new Vue({
  el: "#app",
  components: {
    alertingCheck: AlertingCheck,
  },
  router,
});
