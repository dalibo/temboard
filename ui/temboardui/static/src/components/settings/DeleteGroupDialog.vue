<script setup>
import { Modal } from "bootstrap";
import $ from "jquery";
import { ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";

const props = defineProps(["kind"]);

const root = ref(null);
const error = ref(null);
const waiting = ref(false);
const groupName = ref("");

function open(name) {
  groupName.value = name;
  new Modal(root.value.$el).show();
}

function delete_() {
  waiting.value = true;
  $.ajax({
    url: `/json/groups/${props.kind}/${groupName.value}`,
    type: "DELETE",
    success: function () {
      window.location.reload();
    },
    error: function (xhr) {
      waiting.value = false;
      error.value.fromXHR(xhr);
    },
  });
}

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalDeleteGroup" :title="`Delete ${kind} group properties`" ref="root">
    <div class="modal-body">
      <Error ref="error" :showTitle="false"></Error>
      <p class="text-center">
        <strong>Please confirm the deletion of the following group:</strong>
      </p>
      <div class="alert text-body-secondary mx-auto pa-6">
        <h2 class="text-center">{{ groupName }}</h2>
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
      <button
        id="buttonDeleteGroup"
        class="btn btn-danger ms-auto"
        type="button"
        @click="delete_"
        v-bind:disabled="waiting"
      >
        Yes, delete this group
        <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </ModalDialog>
</template>
