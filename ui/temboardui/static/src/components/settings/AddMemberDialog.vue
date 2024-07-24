<script setup>
import $ from "jquery";
import { computed, onMounted, ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";

const props = defineProps(["groupname"]);
const root = ref(null);
let url = null;

function open() {
  url = `/json/groups/${props.groupname}/members`;
  root.value.show();
}
defineExpose({ open });
const emit = defineEmits(["added"]);

const error = ref(null);
const waiting = ref(true);
const users = ref([]);
const members = ref([]);

function fetch() {
  waiting.value = true;
  $.ajax({
    url: "/json/users",
    success: (data) => {
      users.value = data.map((user) => {
        return {
          name: user.name,
          active: user.active,
          member: user.groups.includes(props.groupname),
        };
      });
    },
    error: (xhr) => {
      error.value.fromXHR(xhr);
    },
  }).always(() => {
    waiting.value = false;
  });
}

const filter = ref("");
const filtered = computed(() => {
  let f = filter.value.toLowerCase();
  return users.value.filter((user) => {
    return f ? user.name.toLowerCase().includes(f) : true;
  });
});

function add(username) {
  waiting.value = true;
  $.ajax({
    url: url,
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ username }),
    success: (data) => {
      root.value.hide();
      emit("added", data);
    },
    error: (xhr) => {
      error.value.fromXHR(xhr);
    },
  }).always(() => {
    waiting.value = false;
  });
}

function reset() {
  filter.value = "";
  waiting.value = true;
}
</script>

<template>
  <ModalDialog ref="root" id="modalAddMember" title="Add Member" @opening="fetch" @closed="reset">
    <div class="modal-body container pb-3">
      <Error ref="error"></Error>
      <div class="row gy-3">
        <div class="col-12">
          <input class="form-control" type="search" placeholder="Search username..." v-model="filter" />
        </div>
        <div class="col-12 overflow-auto" style="max-height: 20rem">
          <div v-if="waiting" class="col-12">
            <p class="text-center">
              Waiting for server.
              <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
            </p>
          </div>
          <div v-if="filtered.length == 0" class="row text-secondary mx-auto p-4">No member matches filter.</div>
          <ul class="list-group" data-testid="members">
            <li v-for="user in filtered" class="list-group-item d-flex justify-content-between align-items-center">
              <button
                class="btn btn-link"
                type="button"
                @click.prevent="add(user.name)"
                :disabled="waiting || !user.active || user.member"
              >
                {{ user.name }}
              </button>
              <i v-if="user.member" class="fa fa-check text-success"></i>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </ModalDialog>
</template>
