<script setup>
import $ from "jquery";
import { onUpdated, ref, watch } from "vue";

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
watch(
  () => props.comment,
  (newValue) => {
    commentModel.value = newValue;
  },
);

onUpdated(() => {
  const tooltipTriggerList = root.value.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((el) => new Tooltip(el));
});

function submit() {
  const plugins = $(root.value)
    .find("input:checkbox[name=plugins]:checked")
    .toArray()
    .map((i) => i.value);
  const data = {
    groups: $("#selectGroups" + props.type).val(),
    plugins: plugins,
    notify: $("#inputNotify" + props.type).is(":checked"),
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
        <div id="divGroups" class="mb-3 col-sm-6" v-if="groups.length > 0">
          <label :for="'selectGroups' + type" class="form-label">Groups</label>
          <select :id="'selectGroups' + type" :disabled="waiting" multiple required>
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
        <div id="divPlugins" class="mb-3 col-sm-6" v-if="plugins.length > 0">
          <label :for="'selectPlugins' + type" class="form-label">Plugins</label>
          <div class="form-check" v-for="plugin of plugins">
            <input
              class="form-check-input"
              type="checkbox"
              :value="plugin.name"
              :id="`pluginCheckbox_${plugin.name}`"
              :checked="plugin.selected"
              :disabled="plugin.disabled ? 'disabled' : null"
              :class="{ disabled: plugin.disabled }"
              :title="plugin.disabled ? 'Plugin disabled by agent.' : null"
              name="plugins"
            />
            <label class="form-check-label" :for="`pluginCheckbox_${plugin.name}`"> {{ plugin.name }} </label>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-sm-12">
          <div class="form-check">
            <input
              :id="'inputNotify' + type"
              class="form-check-input"
              type="checkbox"
              :checked="notify"
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
