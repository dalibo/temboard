<script setup>
import $ from "jquery";
import { ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";

const root = ref(null);
const error = ref(null);
const waiting = ref(false);
const user = ref("");

function open(username) {
  user.value = username;
}

function delete_() {
  waiting.value = true;
  $.ajax({
    url: "/json/settings/delete/user",
    type: "POST",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({ username: user.value }),
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done(() => {
      window.location.reload();
    });
}

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalDeleteUser" title="Delete User" ref="root">
    <div class="modal-body">
      <Error ref="error"></Error>
      <p class="text-center">
        <strong>Please confirm the deletion of the following user: </strong>
      </p>
      <div class="alert text-body-secondary mx-auto pa-6">
        <h2 class="text-center">{{ user }}</h2>
      </div>
    </div>

    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
      <button id="buttonDelete" class="btn btn-danger ms-auto" type="button" @click="delete_" :disabled="waiting">
        Yes, delete this user
        <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </ModalDialog>
</template>
