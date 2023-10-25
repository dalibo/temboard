import Vue from "vue";
import Activity from "./views/Activity.vue";
import BootstrapVue from "bootstrap-vue";
import "bootstrap-vue/dist/bootstrap-vue.css";
Vue.use(BootstrapVue);

new Vue({
  el: "#app",
  components: {
    activity: Activity,
  },
});
