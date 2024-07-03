<script setup>
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
  $(root.value.$el).modal("show");
  groupName.value = name;
  waiting.value = true;
  $.ajax({
    url: ["/json/settings/group", props.kind, name].join("/"),
    type: "get",
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function () {
      waiting.value = false;
    },
    error: function (xhr) {
      error.value.fromXHR(xhr);
    },
  });
}

function delete_() {
  waiting.value = true;
  $.ajax({
    url: "/json/settings/delete/group/" + props.kind,
    type: "post",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({ group_name: groupName.value }),
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
      <div class="alert alert-light mx-auto pa-6">
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
