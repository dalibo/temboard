import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import Home from "./views/Home.vue";

const NotFound = { template: "" };
const router = createRouter({
  history: createWebHistory(),
  // at least one route is required, we use a fake one
  routes: [{ path: "/:pathMatch(.*)*", name: "not-found", component: NotFound }],
});

createApp({
  components: {
    home: Home,
  },
})
  .use(router)
  .mount("#app");
