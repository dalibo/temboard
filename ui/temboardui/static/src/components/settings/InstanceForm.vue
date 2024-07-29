<script setup>
import $ from "jquery";
import { computed, onUpdated, ref, watch, watchEffect } from "vue";
import Multiselect from "vue-multiselect";

import InstanceDetails from "./InstanceDetails.vue";

const props = defineProps([
  "submit_text", // Submit button label.
  "waiting", // Whether parent is interacting with server.
  "type", // Either 'New' or 'Update'

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
const selectedGroups = defineModel("selectedGroups");
const availableGroups = computed(() => props.groups.map((group) => group.name));

watch(
  () => props.comment,
  (newValue) => {
    commentModel.value = newValue;
  },
);

watchEffect(() => {
  selectedGroups.value = props.groups.filter((group) => group.selected).map((group) => group.name);
});

onUpdated(() => {
  const tooltipTriggerList = root.value.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((el) => new Tooltip(el));
});

function submit() {
  // data generates payload for both POST /json/settings/instances and POST
  // /json/settings/instances/X.X.X.X/PPPP.
  const data = {
    // Define parameters.
    groups: selectedGroups.value,
    plugins: $("#selectPlugins" + props.type).val(),
    notify: props.notify,
    comment: commentModel.value,
  };
  emit("submit", data);
}

const emit = defineEmits(["submit"]);
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
        <div id="divGroups" class="mb-3 col-sm-6">
          <label class="form-label">Groups</label>
          <multiselect
            :id="'selectGroups' + type"
            v-model="selectedGroups"
            :options="availableGroups"
            :multiple="true"
            :hide-selected="true"
            :searchable="false"
            select-label=""
          ></multiselect>
          <div id="tooltip-container"></div>
        </div>
        <div id="divPlugins" class="mb-3 col-sm-6" v-if="plugins.length > 0">
          <label :for="'selectPlugins' + type" class="form-label">Plugins</label>
          <select :id="'selectPlugins' + type" :disabled="waiting" multiple="multiple">
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
            <input
              :id="'inputNotify' + type"
              class="form-check-input"
              type="checkbox"
              :value="notify"
              :disabled="waiting"
            />
            <label :for="'inputNotify' + type" class="form-label">Notify users of any status alert.</label>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="mb-3 col-sm-12">
          <label :for="'inputComment' + type" class="form-label">Comment</label>
          <textarea
            :id="'inputComment' + type"
            class="form-control"
            rows="3"
            v-model="commentModel"
            :disabled="waiting"
          >
          </textarea>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
      <button :id="'buttonSubmit' + type" class="btn btn-success ms-auto" type="submit" :disabled="waiting">
        {{ submit_text }}
        <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </form>
</template>
