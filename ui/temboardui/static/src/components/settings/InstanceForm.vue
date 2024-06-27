<script setup>
import { onUpdated, ref, watch } from "vue";

import InstanceDetails from "./InstanceDetails.vue";

const props = defineProps([
  "submit_text", // Submit button label.
  "waiting", // Whether parent is interacting with server.

  // Discover readonly data.
  "pg_host",
  "pg_port",
  "pg_data",
  "pg_version_summary",
  "cpu",
  "mem_gb",
  "signature_status",

  // Agent configuration
  "comment",
  "notify",
  "groups",
  "plugins",
]);

const root = ref(null);
const commentModel = ref(null);
watch(
  () => props.comment,
  (newValue) => {
    commentModel.value = newValue;
  },
);

onUpdated(() => {
  $('[data-toggle="tooltip"]', root.value.$el).tooltip();
  if ($("#selectGroups").data("multiselect")) {
    $("#selectGroups").multiselect(props.waiting ? "disable" : "enable");
    $("#selectPlugins").multiselect(props.waiting ? "disable" : "enable");
  }
});

function setup_multiselects() {
  // jQuery multiselect plugin must be called once Vue template is rendered.
  const options = {
    templates: {
      button: `
            <button type="button"
                    class="multiselect dropdown-toggle border-secondary"
                    data-toggle="dropdown">
              <span class="multiselect-selected-text"></span> <b class="caret"></b>
            </button>
            `,
      li: `
            <li class="dropdown-item">
              <label class="w-100"></label>
            </li>
            `,
    },
    numberDisplayed: 1,
  };
  $("#selectGroups").multiselect(options);
  $("#selectPlugins").multiselect(options);
}

function teardown_multiselects() {
  $("#selectGroups").multiselect("destroy");
  $("#selectPlugins").multiselect("destroy");
}

function submit() {
  // data generates payload for both POST /json/settings/instances and POST
  // /json/settings/instances/X.X.X.X/PPPP.
  const data = {
    // Define parameters.
    groups: $("#selectGroups").val(),
    plugins: $("#selectPlugins").val(),
    notify: props.notify,
    comment: commentModel.value,
  };
  emit("submit", data);
}

const emit = defineEmits(["submit"]);
defineExpose({ setup_multiselects, teardown_multiselects });
</script>

<template>
  <form v-on:submit.prevent="submit" ref="root">
    <div class="modal-body p-3">
      <div class="row">
        <InstanceDetails
          :pg_host="pg_host"
          :pg_port="pg_port"
          :pg_version_summary="pg_version_summary"
          :pg_data="pg_data"
          :cpu="cpu"
          :mem_gb="mem_gb"
        />
      </div>

      <div class="row" v-if="$slots.default">
        <div class="col">
          <!-- Error slot -->
          <slot></slot>
        </div>
      </div>

      <div class="row">
        <div id="divGroups" class="form-group col-sm-6" v-if="groups.length > 0">
          <label for="selectGroups">Groups</label>
          <select id="selectGroups" :disabled="waiting" multiple required>
            <option
              v-for="group of groups"
              :key="group.name"
              :selected="group.selected ? 'selected' : null"
              :value="group.name"
            >
              {{ group.name }}
            </option>
          </select>
          <div id="tooltip-container"></div>
        </div>
        <div id="divPlugins" class="form-group col-sm-6" v-if="plugins.length > 0">
          <label for="selectPlugins" class="control-label">Plugins</label>
          <select id="selectPlugins" :disabled="waiting" multiple="multiple">
            <option
              v-for="plugin of plugins"
              :key="plugin.name"
              :value="plugin.name"
              :selected="plugin.selected"
              :disabled="plugin.disabled ? 'disabled' : null"
              :class="{ disabled: plugin.disabled }"
              :title="plugin.disabled ? 'Plugin disabled by agent.' : null"
            >
              {{ plugin.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="row">
        <div class="col-sm-12">
          <div class="form-check">
            <input id="inputNotify" class="form-check-input" type="checkbox" v-model="notify" :disabled="waiting" />
            <label for="inputNotify" class="control-label">Notify users of any status alert.</label>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="form-group col-sm-12">
          <label for="inputComment" class="control-label">Comment</label>
          <textarea id="inputComment" class="form-control" rows="3" v-model="commentModel" :disabled="waiting">
          </textarea>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>
      <button id="buttonSubmit" class="btn btn-success ml-auto" type="submit" :disabled="waiting">
        {{ submit_text }}
        <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </form>
</template>
