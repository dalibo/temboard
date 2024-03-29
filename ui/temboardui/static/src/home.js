import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import Home from "./views/Home.vue";

const router = createRouter({
  routes: [],
  history: createWebHistory(),
});

createApp({
  components: {
    home: Home,
  },
})
  .use(router)
  .mount("#app");
