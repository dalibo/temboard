<script setup>
import DataTablesLib from "datatables.net-bs5";
import "datatables.net-buttons-bs5";
import DataTable from "datatables.net-vue3";
import $ from "jquery";
import { onMounted, onUpdated, ref } from "vue";

import DeleteDialog from "../DeleteDialog.vue";
import AddMemberDialog from "./AddMemberDialog.vue";

DataTable.use(DataTablesLib);
const props = defineProps(["environment"]);
const deleteModal = ref(null);
const addModal = ref(null);
const waiting = ref(true);

const dba_group = ref("");
const memberships = ref([]);
const columns = [
  { width: "auto" }, // username
  { width: "10rem", className: "text-secondary text-center", orderable: false, searchable: false }, // profile
  {
    // action
    width: "4rem",
    className: "text-center",
    orderable: false,
    searchable: false,
  },
];
const options = {
  layout: {
    topStart: "search",
    topEnd: {
      buttons: [
        {
          className: "btn btn-sm btn-success",
          text: "Add Member",
          attr: {
            "data-testid": "add",
          },
          action: () => {
            addModal.value.open();
          },
        },
      ],
    },
  },
};

onMounted(() => {
  // Save an AJAX call by rebuilding the group name.
  dba_group.value = `${props.environment}/dba`;
  fetch();
});

function fetch() {
  waiting.value = true;
  // Don't use DataTable ajax source to handle errors and spinner.
  $.ajax({
    url: `/json/environments/${props.environment}/members`,
    success: function (data) {
      memberships.value = data;
    },
    error: window.showError,
  }).always(() => {
    waiting.value = false;
  });
}
</script>

<template>
  <div class="row">
    <h5 class="col h5">Environment {{ environment }}'s Members</h5>
  </div>
  <div class="row" v-if="waiting">
    <div class="col text-center">
      <i class="fa-solid fa-spinner fa-spin loader"></i>
      <span>Loading...</span>
    </div>
  </div>
  <div class="row">
    <DataTable
      class="table table-striped table-bordered table-hover"
      :data="memberships"
      :columns="columns"
      :options="options"
    >
      <thead>
        <tr>
          <th>Username</th>
          <th>Profile</th>
          <th></th>
        </tr>
      </thead>

      <template #column-0="{ rowData }">
        {{ rowData.username }}
      </template>
      <template #column-1="{ rowData }">
        {{ rowData.profile }}
      </template>
      <template #column-2="{ rowData }">
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm buttonDelete m-1"
          title="Delete"
          @click.prevent="$refs.deleteModal.open(`/json/groups/${rowData.groupname}/members/${rowData.username}`)"
        >
          <i class="fa-solid fa-trash"></i>
        </button>
      </template>
    </DataTable>
  </div>

  <DeleteDialog ref="deleteModal" title="Exclude user" v-slot="{ resource }" :noreload="true" @done="fetch">
    <p class="fs-5 text-center">
      Please confirm the exclusion of user <strong>{{ resource.username }}</strong> from {{ environment }}.
    </p>
  </DeleteDialog>

  <AddMemberDialog ref="addModal" :groupname="dba_group" @added="fetch"></AddMemberDialog>
</template>
