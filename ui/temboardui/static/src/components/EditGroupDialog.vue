<script setup>
import { Modal } from "bootstrap";
import $ from "jquery";
import { ref } from "vue";

import Error from "./Error.vue";
import ModalDialog from "./ModalDialog.vue";

const props = defineProps(["kind"]);

const root = ref(null);
const error = ref(null);
const waiting = ref(false);
const initName = ref("");
const name = ref("");
const description = ref("");
const roleGroups = ref([]);
const allRoleGroups = ref([]);

function open(openName) {
  reset();
  initName.value = openName;
  name.value = openName;
  new Modal(root.value.$el).show();

  if (props.kind == "instance") {
    waiting.value = true;
    $.ajax({
      url: "/json/groups/role",
      contentType: "application/json",
      error: ajaxError,
      success: function (data) {
        allRoleGroups.value = data;
        waiting.value = false;
      },
    });
  }

  if (!initName.value) {
    return;
  }

  waiting.value = true;
  $.ajax({
    url: `/json/groups/${props.kind}/${initName.value}`,
    contentType: "application/json",
    error: ajaxError,
    success: function (data) {
      description.value = data.description;
      if (props.kind == "instance") {
        roleGroups.value = data.role_groups;
      }
      waiting.value = false;
    },
  });
}

function submit() {
  const data = {
    name: name.value,
    description: description.value,
    role_groups: $("#selectGroups").val(),
  };

  let url = `/json/groups/${props.kind}`;
  if (initName.value) {
    url += `/${initName.value}`;
  }
  waiting.value = true;
  $.ajax({
    url: url,
    type: initName.value ? "PUT" : "POST",
    data: JSON.stringify(data),
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
  name.value = "";
  description.value = "";
  roleGroups.value = [];
  initName.value = false;
  waiting.value = false;
}

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalEditGroup" :title="`${initName ? 'Update' : 'Create'} ${kind} group`" ref="root">
    <form @submit.prevent="submit">
      <div class="modal-body p-3">
        <div class="row">
          <div class="col">
            <Error ref="error" :showTitle="false"></Error>
          </div>
        </div>
        <div class="row">
          <div class="mb-3 col-sm-6">
            <label for="inputNewGroupname" class="form-label">Group name</label>
            <input
              type="text"
              class="form-control"
              id="inputNewGroupname"
              placeholder="New group name"
              v-model="name"
            />
          </div>
          <template v-if="kind == 'instance'">
            <div class="mb-3 col-sm-6">
              <label for="selectGroups" class="form-label">User groups</label><br />
              <select id="selectGroups" multiple="multiple">
                <option
                  v-for="group of allRoleGroups"
                  :value="group.name"
                  :selected="roleGroups.includes(group.name)"
                  :key="group.key"
                >
                  {{ group.name }}
                </option>
              </select>
              <p class="form-text text-body-secondary">
                Please select the user groups allowed to view instances from this instance group.
              </p>
            </div>
          </template>
        </div>
        <div class="row">
          <div class="mb-3 col-sm-12">
            <label for="inputDescription" class="form-label">Description</label>
            <textarea
              class="form-control"
              rows="3"
              placeholder="Description"
              id="inputDescription"
              v-model="description"
              >{{ description }}</textarea
            >
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
        <button id="buttonSubmit" class="btn btn-success ms-auto" type="submit" v-bind:disabled="waiting">
          {{ initName ? "Update" : "Create" }}
          <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
        </button>
      </div>
    </form>
  </ModalDialog>
</template>
