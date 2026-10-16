import { createApp } from "vue";

import InstanceExplain from "./views/InstanceExplain.vue";

createApp({
  components: {
    "instance-explain": InstanceExplain,
  },
}).mount("#app");
