/* global instances, isAdmin, Vue */
import Vue from "vue";
import VueRouter from "vue-router";

import InstanceList from "./components/home/InstanceList.vue";

Vue.use(VueRouter);

new Vue({
  el: "#app",
  router: new VueRouter(),
  components: {
    "instance-list": InstanceList,
  },
});
