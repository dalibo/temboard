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
const groupDescription = ref("");
const groups = ref([]);
const groupInGroups = ref([]);
const isNew = ref(false);
let initialName = undefined;

function open(name) {
  error.value.clear();
  initialName = name;
  isNew.value = !name;
  $(root.value.$el).modal("show");
  groupName.value = name;
  waiting.value = true;

  // First reset form
  groupName.value = "";
  groupDescription.value = "";
  groups.value = [];
  groupInGroups.value = [];

  const url = name ? ["/json/settings/group", props.kind, name].join("/") : "/json/settings/all/group/role";
  $.ajax({
    url: url,
    type: "get",
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      // Then load new data
      if (name) {
        groupName.value = data.name;
        groupDescription.value = data.description;
        if (props.kind == "instance") {
          groups.value = data.user_groups;
          groupInGroups.value = data.in_groups;
        }
      } else {
        groups.value = data.groups;
      }
      waiting.value = false;
    },
    error: function (xhr) {
      error.value.fromXHR(xhr);
    },
  });
}

function submit() {
  const data = {
    new_group_name: groupName.value,
    description: groupDescription.value,
  };

  if (props.kind == "instance") {
    Object.assign(data, { user_groups: $("#selectGroups").val() });
  }

  waiting.value = true;
  const parts = ["/json/settings/group", props.kind];
  if (!isNew.value) {
    parts.push(initialName);
  }
  $.ajax({
    url: parts.join("/"),
    type: "post",
    data: JSON.stringify(data),
    async: true,
    contentType: "application/json",
    dataType: "json",
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
  <ModalDialog id="modalUpdateGroup" :title="`${isNew ? 'Create' : 'Update'} ${kind} group`" ref="root">
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
              v-model="groupName"
            />
          </div>
          <template v-if="kind == 'instance'">
            <div class="mb-3 col-sm-6">
              <label for="selectGroups" class="form-label">User groups</label><br />
              <select id="selectGroups" multiple="multiple">
                <option
                  v-for="group of groups"
                  :value="group.name"
                  :selected="groupInGroups.includes(group.name)"
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
              v-model="groupDescription"
              >{{ groupDescription }}</textarea
            >
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
        <button id="buttonSubmit" class="btn btn-success ms-auto" type="submit" v-bind:disabled="waiting">
          {{ isNew ? "Create" : "Update" }}
          <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
        </button>
      </div>
    </form>
  </ModalDialog>
</template>
