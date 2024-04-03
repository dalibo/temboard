import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import AlertingCheck from "./views/AlertingCheck.vue";

const NotFound = { template: "" };
const router = createRouter({
  history: createWebHistory(),
  // at least one route is required, we use a fake one
  routes: [{ path: "/:pathMatch(.*)*", name: "not-found", component: NotFound }],
});

createApp({
  components: {
    alertingCheck: AlertingCheck,
  },
})
  .use(router)
  .mount("#app");
