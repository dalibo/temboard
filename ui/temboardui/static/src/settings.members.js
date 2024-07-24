import { createApp } from "vue";

import MembersPage from "./components/settings/MembersPage.vue";

createApp({
  components: {
    memberspage: MembersPage,
  },
}).mount("#members-app");
