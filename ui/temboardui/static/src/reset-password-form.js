import { createApp } from "vue";

import ResetPasswordForm from "./views/ResetPasswordForm.vue";

createApp(ResetPasswordForm, {
  token: document.getElementById("app").dataset.token,
}).mount("#app");
