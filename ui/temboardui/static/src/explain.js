import { createApp } from "vue";

import Explain from "./views/Explain.vue";

createApp({
  components: {
    explain: Explain,
  },
}).mount("#app");
