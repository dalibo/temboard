<script setup>
import $ from "jquery";
import { computed, onUpdated, ref, watch, watchEffect } from "vue";
import Multiselect from "vue-multiselect";

import InstanceDetails from "./InstanceDetails.vue";

const props = defineProps([
  "submit_text", // Submit button label.
  "waiting", // Whether parent is interacting with server.
  "disabled",
  "type", // Either 'New' or 'Update'
  "environments",

  // Discover readonly data.
  "pg_host",
  "pg_port",
  "pg_data",
  "pg_version_summary",
  "cpu",
  "mem_gb",
  "signature_status",

  // Instance configuration
  "comment",
  "notify",
  "environment",
  "plugins",
]);

const root = ref(null);
const instance = ref({
  environment: props.environment,
  comment: props.comment,
  notify: props.notify,
});

watchEffect(() => {
  instance.value.environment = props.environment;
  instance.value.comment = props.comment;
  instance.value.notify = props.notify;
});

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
    ...instance.value,
    plugins: plugins,
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
        <div class="col-sm-6">
          <div class="row">
            <div class="col">
              <label class="form-label">Environment</label>
              <select :id="'selectEnvironment' + type" v-model="instance.environment" class="form-select">
                <template v-for="e in props.environments">
                  <option :value="e.name" :title="e.description">
                    {{ e.name }}
                  </option>
                </template>
              </select>
              <div id="tooltip-container"></div>
            </div>
          </div>
          <div class="row pt-3">
            <div class="col-sm-12">
              <div class="form-check">
                <input
                  :id="'inputNotify' + type"
                  class="form-check-input"
                  type="checkbox"
                  v-model="instance.notify"
                  :disabled="waiting"
                />
                <label :for="'inputNotify' + type" class="form-label">Notify users of any status alert.</label>
              </div>
            </div>
          </div>
        </div>
        <div id="divPlugins" class="col-sm-6" v-if="plugins.length > 0">
          <label :for="'selectPlugins' + type" class="form-label">Plugins</label>
          <div class="form-check" v-for="plugin of plugins">
            <input
              class="form-check-input"
              type="checkbox"
              :value="plugin.name"
              :id="`pluginCheckbox_${plugin.name}`"
              :checked="plugin.selected"
              :disabled="disabled || plugin.disabled"
              :class="{ disabled: plugin.disabled }"
              :title="plugin.disabled ? 'Plugin disabled by agent.' : null"
              name="plugins"
            />
            <label class="form-check-label" :for="`pluginCheckbox_${plugin.name}`"> {{ plugin.name }} </label>
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
            v-model="instance.comment"
            :disabled="waiting"
          >
          </textarea>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
      <button :id="'buttonSubmit' + type" class="btn btn-success ms-auto" type="submit" :disabled="disabled">
        {{ submit_text }}
        <i v-if="waiting" class="fa-solid fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </form>
</template>
