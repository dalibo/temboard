import { createApp } from "vue";

import ResetPasswordForm from "./views/ResetPasswordForm.vue";

createApp(ResetPasswordForm, {
  token: document.querySelector("#app").dataset.token,
}).mount("#app");
