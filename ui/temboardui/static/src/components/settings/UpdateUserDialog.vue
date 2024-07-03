<script setup>
import $ from "jquery";
import { reactive, ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";

const error = ref(null);
const waiting = ref(false);
const groups = ref([]);
let currentUsername = null;
const isNew = ref(false);

const userModel = reactive({
  new_username: "",
  email: "",
  phone: "",
  password: "",
  password2: "",
  groups: [],
  is_active: false,
  is_admin: false,
});

function open(username) {
  // Reset dialog state.
  if (error.value) {
    error.value.clear();
  }
  waiting.value = true;

  // Configure for target user data.
  currentUsername = username;
  isNew.value = !username;

  const url = username ? "/json/settings/user/" + username : "/json/settings/all/group/role";

  // First reset the form
  userModel.new_username = "";
  userModel.email = "";
  userModel.phone = "";
  userModel.password = "";
  userModel.password2 = "";
  userModel.groups = [];
  userModel.is_active = true;
  userModel.is_admin = false;
  groups.value = [];

  $.ajax({
    url: url,
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done((data) => {
      groups.value = data.groups.map((group) => ({
        name: group.name,
        description: group.description,
        disabled: false,
        selected: username ? data.in_groups.includes(group.name) : false,
      }));

      if (username) {
        userModel.new_username = data.role_name;
        userModel.email = data.role_email;
        userModel.phone = data.role_phone;
        userModel.is_active = data.is_active;
        userModel.is_admin = data.is_admin;
        userModel.groups = groups.value.filter((group) => group.selected).map((group) => group);
      }

      waiting.value = false;
    });
}

function submit() {
  const data = { ...userModel };
  Object.assign(data, { groups: $("#selectGroups").val() });
  waiting.value = true;
  let url_request = "/json/settings/user";
  if (!isNew.value) {
    url_request = url_request + "/" + currentUsername;
  }
  $.ajax({
    url: url_request,
    method: "POST",
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
          <div class="form-group col-sm-6">
            <label class="control-label"
              >Username<input type="text" class="form-control" placeholder="Username" v-model="userModel.new_username"
            /></label>
          </div>
          <div class="form-group col-sm-6">
            <label class="control-label"
              >Email<input type="email" class="form-control" placeholder="Email" v-model="userModel.email"
            /></label>
            <span class="form-text text-muted small"
              >Leave blank to prevent user from receiving notifications by email.</span
            >
          </div>
        </div>

        <div class="row">
          <div class="form-group col-sm-6">
            <label class="control-label"
              >Password&#42;
              <input type="password" class="form-control" placeholder="Password" v-model="userModel.password" />
              <input
                type="password"
                class="form-control"
                placeholder="Confirm password"
                v-model="userModel.password2"
              />
            </label>
            <p class="form-text text-muted"><small>&#42;: leave this field blank to keep it unchanged.</small></p>
          </div>

          <div class="form-group col-sm-6" v-if="groups.length > 0">
            <label class="control-label">
              Groups<br />
              <select id="selectGroups" multiple="multiple">
                <option
                  v-for="group of groups"
                  :value="group.name"
                  :selected="userModel.groups.includes(group)"
                  :key="group.key"
                >
                  {{ group.name }}
                </option>
              </select> </label
            ><br />
            <div class="custom-control custom-switch">
              <br />
              <input type="checkbox" class="custom-control-input" id="switchActive" v-model="userModel.is_active" />
              <label class="custom-control-label" for="switchActive">Active</label><br />
            </div>
            <div class="custom-control custom-switch">
              <br />
              <input type="checkbox" class="custom-control-input" id="switchAdmin" v-model="userModel.is_admin" />
              <label class="custom-control-label" for="switchAdmin">Administrator</label><br />
            </div>
          </div>
        </div>

        <div class="row">
          <div class="form-group col-sm-6">
            <label class="control-label"
              >Phone
              <input type="text" class="form-control" placeholder="Phone" v-model="userModel.phone" />
            </label>
            <span class="form-text text-muted small"
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
