import BootstrapVue from "bootstrap-vue";
import "bootstrap-vue/dist/bootstrap-vue.css";
import * as _ from "lodash";
import Vue from "vue";
import VueRouter from "vue-router";

import Statements from "./views/Statements.vue";

const router = new VueRouter();

Vue.use(VueRouter);

Vue.use(BootstrapVue);

new Vue({
  el: "#app",
  components: {
    statements: Statements,
  },
  router,
});
