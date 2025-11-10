<script setup>
import $ from "jquery";
import { computed, ref } from "vue";

import Error from "./Error.vue";
import ModalDialog from "./ModalDialog.vue";

const root = ref(null);
const error = ref(null);
const waiting = ref(true);
const failed = ref(false);
const editedName = ref("");
const disabled = computed(() => waiting.value || failed.value);
const verb = computed(() => (editedName.value ? "Update" : "Create"));
let initialModel = {
  name: "",
  description: "",
};
const model = ref({ ...initialModel });

let url = "/json/environments";

function edit(name) {
  editedName.value = name;
  model.value.name = name;
  root.value.show();
}

defineExpose({ edit });

function fetch() {
  if (editedName.value) {
    url = `/json/environments/${editedName.value}`;
  } else {
    waiting.value = false;
    return;
  }

  waiting.value = true;
  $.ajax({
    url: url,
    contentType: "application/json",
    error: ajaxError,
    success: function (data) {
      model.value.description = data.description;
      waiting.value = false;
    },
  });
}

function submit() {
  waiting.value = true;
  $.ajax({
    url: url,
    type: editedName.value ? "PUT" : "POST",
    data: JSON.stringify(model.value),
    contentType: "application/json",
    error: ajaxError,
    success: function () {
      window.location.reload();
    },
  });
}

function ajaxError(xhr) {
  error.value.fromXHR(xhr);
  waiting.value = false;
}

function reset() {
  error.value.clear();
  waiting.value = true;
  failed.value = false;
  editedName.value = "";
  Object.assign(model.value, initialModel);
  url = "/json/environments";
}
</script>

<template>
  <ModalDialog ref="root" id="modalEditEnvironment" :title="`${verb} environment`" @opening="fetch" @closed="reset">
    <form @submit.prevent="submit">
      <div class="modal-body p-3">
        <div class="row">
          <div class="col">
            <Error ref="error" :showTitle="false"></Error>
          </div>
        </div>
        <div class="row">
          <div class="mb-3 col-sm-6">
            <label for="inputName" class="form-label">Name</label>
            <input
              type="text"
              class="form-control"
              id="inputName"
              placeholder="Environment name"
              :disabled="disabled"
              v-model="model.name"
            />
          </div>
        </div>
        <div class="row">
          <div class="mb-3 col-sm-12">
            <label for="inputDescription" class="form-label">Description</label>
            <textarea
              class="form-control"
              rows="3"
              placeholder="Description"
              id="inputDescription"
              v-model="model.description"
              :disabled="disabled"
              >{{ model.description }}</textarea
            >
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
        <button id="buttonSubmit" class="btn btn-success ms-auto" type="submit" v-bind:disabled="waiting">
          {{ verb }}
          <i v-if="waiting" class="fa-solid fa-spinner fa-spin loader"></i>
        </button>
      </div>
    </form>
  </ModalDialog>
</template>
