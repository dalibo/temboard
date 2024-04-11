import Vue from "vue";

import DeleteUserDialog from "./components/settings/DeleteUserDialog.vue";
import UpdateUserDialog from "./components/settings/UpdateUserDialog.vue";

new Vue({
  el: "#app",
  components: {
    "update-user-dialog": UpdateUserDialog,
    "delete-user-dialog": DeleteUserDialog,
  },
});
