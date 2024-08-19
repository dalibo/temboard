<script setup>
// A resource deletion dialog
//
// Fetch resource, present a confirmation dialog and delete the resource if the user confirms.
// Use GET or DELETE verb on same resource URL.
// Reload the page after successful deletion.
import { Modal } from "bootstrap";
import $ from "jquery";
import { ref } from "vue";

import Error from "./Error.vue";
import ModalDialog from "./ModalDialog.vue";

defineProps(["id", "title"]);

const root = ref(null);
const error = ref(null);
const failed = ref(false);
const waiting = ref(false);
const resource = ref(null);
let deleteUrl = null;

function open(url) {
  deleteUrl = url;
  error.value.clear();

  new Modal(root.value.$el).show();

  waiting.value = true;
  $.ajax({
    url: url,
    success: (data) => {
      resource.value = data;
    },
    error: (xhr) => {
      error.value.fromXHR(xhr);
      failed.value = true;
    },
  }).always(() => {
    waiting.value = false;
  });
}

function submit() {
  waiting.value = true;
  $.ajax({
    url: deleteUrl,
    type: "DELETE",
    error: (xhr) => {
      error.value.fromXHR(xhr);
    },
    success: () => {
      window.location.reload();
    },
  }).always(() => {
    waiting.value = false;
  });
}

defineExpose({ open });
</script>

<template>
  <ModalDialog :id="id" :title="title" ref="root">
    <div class="modal-body">
      <Error ref="error" :showTitle="false"></Error>
      <slot v-if="resource" :resource="resource"
        ><p class="fs-5 text-center">Please confirm the deletion of the selected resource.</p></slot
      >
    </div>

    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
      <button
        id="buttonDelete"
        class="btn btn-danger ms-auto"
        type="button"
        @click="submit"
        :disabled="waiting || failed"
      >
        Yes, delete
        <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </ModalDialog>
</template>
