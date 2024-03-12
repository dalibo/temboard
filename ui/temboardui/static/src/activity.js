import BootstrapVue from "bootstrap-vue";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Vue from "vue";

import Activity from "./views/Activity.vue";

Vue.use(BootstrapVue);

new Vue({
  el: "#app",
  components: {
    activity: Activity,
  },
});
