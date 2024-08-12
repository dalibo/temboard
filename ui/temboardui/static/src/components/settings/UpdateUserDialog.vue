<script setup>
import $ from "jquery";
import { reactive, ref } from "vue";
import Multiselect from "vue-multiselect";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";

const error = ref(null);
const waiting = ref(false);
const availableGroups = ref([]);
let currentUsername = null;
const isNew = ref(false);

const userModel = reactive({
  name: "",
  email: "",
  phone: "",
  password: "",
  password2: "",
  groups: [],
  is_active: false,
  is_admin: false,
});

function open(username) {
  error.value.clear();
  waiting.value = true;
  userModel.name = "";
  userModel.email = "";
  userModel.phone = "";
  userModel.password = "";
  userModel.password2 = "";
  userModel.groups = [];
  userModel.is_active = true;
  userModel.is_admin = false;

  // Configure for target user data.
  currentUsername = username;
  isNew.value = !username;

  $.ajax({
    url: "/json/groups/role",
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done((data) => {
      availableGroups.value = data.map((group) => group.name);
      waiting.value = false;
    });

  if (!username) {
    return;
  }

  $.ajax({
    url: `/json/users/${username}`,
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done((data) => {
      userModel.name = data.name;
      userModel.email = data.email;
      userModel.phone = data.phone;
      userModel.is_active = data.active;
      userModel.is_admin = data.admin;
      userModel.groups = data.groups;
      waiting.value = false;
    });
}

function submit() {
  const data = { new_username: userModel.name, ...userModel };
  waiting.value = true;
  let endpoint;
  if (isNew.value) {
    endpoint = "/json/settings/user";
  } else {
    endpoint = `/json/users/${currentUsername}`;
  }
  $.ajax({
    url: endpoint,
    method: isNew.value ? "POST" : "PUT",
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

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalUpdateUser" :title="`${isNew ? 'Create' : 'Update'} User`">
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
              >Username<input type="text" class="form-control" placeholder="Username" v-model="userModel.name"
            /></label>
          </div>
          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Email<input type="email" class="form-control" placeholder="Email" v-model="userModel.email"
            /></label>
            <span class="form-text text-body-secondary small"
              >Leave blank to prevent user from receiving notifications by email.</span
            >
          </div>
        </div>

        <div class="row">
          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Password&#42;
              <input type="password" class="form-control" placeholder="Password" v-model="userModel.password" />
              <input
                type="password"
                class="form-control"
                placeholder="Confirm password"
                v-model="userModel.password2"
              />
            </label>
            <p class="form-text text-body-secondary">
              <small>&#42;: leave this field blank to keep it unchanged.</small>
            </p>
          </div>

          <div class="mb-3 col-sm-6">
            <div class="mb-3">
              <label class="form-label"> Groups </label>
              <multiselect
                id="groups"
                v-model="userModel.groups"
                :options="availableGroups"
                :multiple="true"
                :hide-selected="true"
                :searchable="false"
                select-label=""
              ></multiselect>
            </div>
            <div class="form-check form-switch">
              <input
                type="checkbox"
                class="form-check-input"
                role="switch"
                id="switchActive"
                v-model="userModel.is_active"
              />
              <label class="form-check-label" for="switchActive">Active</label><br />
            </div>
            <div class="form-check form-switch">
              <input
                type="checkbox"
                class="form-check-input"
                role="switch"
                id="switchAdmin"
                v-model="userModel.is_admin"
              />
              <label class="form-check-label" for="switchAdmin">Administrator</label><br />
            </div>
          </div>
        </div>

        <div class="row">
          <div class="mb-3 col-sm-6">
            <label class="form-label"
              >Phone
              <input type="text" class="form-control" placeholder="+33..." v-model="userModel.phone" />
            </label>
            <span class="form-text text-body-secondary small"
              >Leave blank to prevent user from receiving notifications by SMS.</span
            >
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-success" :disabled="waiting">
            Save
            <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
          </button>
        </div>
      </div>
    </form>
  </ModalDialog>
</template>
