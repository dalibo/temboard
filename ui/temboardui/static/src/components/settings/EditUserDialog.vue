<script setup>
import $ from "jquery";
import { computed, reactive, ref } from "vue";
import Multiselect from "vue-multiselect";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";

const root = ref(null);
const error = ref(null);
const waiting = ref(true); // Disable controls by default.
const failed = ref(false);
const disabled = computed(() => waiting.value || failed.value);
const availableGroups = ref([]);
const editedName = ref("");
let url = "/json/users";
let initialModel = {
  name: "",
  email: "",
  phone: "",
  password: "",
  password2: "",
  groups: [],
  is_active: true,
  is_admin: false,
};
const model = reactive({ ...initialModel });

function edit(username) {
  editedName.value = username;
  url = `/json/users/${username}`;
  root.value.show();
}

defineExpose({ edit });

function fetch() {
  waiting.value = true;
  $.ajax({
    url: "/json/groups/role",
    error: (xhr) => {
      error.value.fromXHR(xhr);
    },
    success: (data) => {
      availableGroups.value = data.map((group) => group.name);
    },
  }).always(() => {
    waiting.value = false;
  });

  if (!editedName.value) {
    return;
  }

  waiting.value = true;
  $.ajax({
    url,
    error: (xhr) => {
      error.value.fromXHR(xhr);
      failed.value = true;
    },
    success: (data) => {
      model.name = data.name;
      model.email = data.email;
      model.phone = data.phone;
      model.is_active = data.active;
      model.is_admin = data.admin;
      model.groups = data.groups;
    },
  }).always(() => {
    waiting.value = false;
  });
}

function submit() {
  const data = { new_username: model.name, ...model };
  waiting.value = true;
  failed.value = false;
  $.ajax({
    url,
    method: editedName.value ? "PUT" : "POST",
    async: true,
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify(data),
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done(() => {
      window.location.reload();
    });
}

function reset() {
  url = "/json/users";
  editedName.value = "";
  error.value.clear();
  waiting.value = true;
  failed.value = false;
  Object.assign(model, initialModel);
}
</script>

<template>
  <ModalDialog
    ref="root"
    id="modalEditUser"
    :title="`${editedName ? 'Update' : 'Create'} User`"
    @opened="fetch"
    @closed="reset"
  >
    <form v-on:submit.prevent="submit">
      <div class="modal-body p-3">
        <div class="row">
          <div class="col">
            <Error ref="error"></Error>
          </div>
        </div>
        <div class="row">
          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Username<input
                type="text"
                class="form-control"
                placeholder="Username"
                v-model="model.name"
                :disabled="disabled"
            /></label>
          </div>
          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Password&#42;

              <input
                type="password"
                class="form-control"
                placeholder="Password"
                v-model="model.password"
                :disabled="disabled"
              />
              <input
                type="password"
                class="form-control"
                placeholder="Confirm password"
                v-model="model.password2"
                :disabled="disabled"
              />
            </label>
            <p v-if="editedName" class="form-text text-body-secondary">
              <small>&#42;: leave this field blank to keep it unchanged.</small>
            </p>
          </div>

          <div class="mb-3 col-sm-6">
            <div class="mb-3">
              <label class="form-label">Groups</label>
              <multiselect
                id="groups"
                v-model="model.groups"
                :options="availableGroups"
                :multiple="true"
                :hide-selected="true"
                :searchable="false"
                select-label=""
              ></multiselect>
            </div>
          </div>

          <div class="mb-3 col-sm-6">
            <div class="form-check form-switch">
              <input
                type="checkbox"
                class="form-check-input"
                role="switch"
                id="switchActive"
                v-model="model.is_active"
                :disabled="disabled"
              />
              <label class="form-check-label" for="switchActive">Active</label><br />
            </div>
            <div class="form-check form-switch">
              <input
                type="checkbox"
                class="form-check-input"
                role="switch"
                id="switchAdmin"
                v-model="model.is_admin"
                :disabled="disabled"
              />
              <label class="form-check-label" for="switchAdmin">Administrator</label><br />
            </div>
          </div>

          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Email<input
                type="email"
                class="form-control"
                placeholder="Email"
                v-model="model.email"
                :disabled="disabled"
            /></label>
            <span class="form-text text-body-secondary small"
              >Leave blank to prevent user from receiving notifications by email.</span
            >
          </div>

          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Phone
              <input type="text" class="form-control" placeholder="+33..." v-model="model.phone" :disabled="disabled" />
            </label>
            <span class="form-text text-body-secondary small"
              >Leave blank to prevent user from receiving notifications by SMS.</span
            >
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="submit" class="btn btn-success ms-auto" :disabled="disabled">
          Save
          <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
        </button>
      </div>
    </form>
  </ModalDialog>
</template>
