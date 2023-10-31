<script setup>
/**
 * A Bootstrap dialog editing instance properties.
 *
 * Supports temBoard 7.X agent with key. Discover before registration to
 * render a preview of the managed instance. Disables plugins not loaded in
 * agent.
 */

import { computed, nextTick, onUpdated, reactive, ref } from "vue";
import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";
import InstanceForm from "./InstanceForm.vue";

const root = ref(null);
const error = ref(null);
const formCmp = ref(null);
const waiting = ref(false);
const initialForm = {
  agent_key: "",
  comment: "",
  notify: true,
  cpu: null,
  server_groups: [],
  current_groups: [],
  mem_gb: null,
  pg_data: null,
  pg_host: null,
  pg_port: null,
  pg_version_summary: null,
  server_plugins: [],
  current_plugins: [],
  agent_plugins: [],
  signature_status: null,
};
const form = reactive({ ...initialForm });
let agent_address = null;
let agent_port = null;
let discover_data;
let discover_etag;

const plugins = computed(() => {
  return Array.from(form.server_plugins, (name) => {
    return {
      name,
      disabled: form.agent_plugins.length > 0 && form.agent_plugins.indexOf(name) === -1,
      selected: form.current_plugins.indexOf(name) !== -1,
    };
  });
});

const groups = computed(() => {
  return Array.from(form.server_groups, (group) => {
    return {
      name: group.name,
      selected: form.current_groups.indexOf(group.name) !== -1,
    };
  });
});

onUpdated(() => {
  $('[data-toggle="tooltip"]', root.value.$el).tooltip();
  if ($("#selectGroups").data("multiselect")) {
    $("#selectGroups").multiselect(waiting.value ? "disable" : "enable");
    $("#selectPlugins").multiselect(waiting.value ? "disable" : "enable");
  }
});

function discover_agent() {
  return $.ajax({
    url: ["/json/discover/instance", agent_address, agent_port].join("/"),
    type: "get",
    contentType: "application/json",
    dataType: "json",
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done((data, _, xhr) => {
      if ("invalid" == data.signature_status) {
        error.value.setHTML(`
              <p><strong>Signature missmatch !</strong></p>

              <p>Agent is not configured for this UI. You must accept
              <strong>this</strong> UI signing key in agent configuration. See
              installation documentation.</p>
            `);
        waiting.value = false;
        return;
      }

      discover_data = data;
      discover_etag = xhr.getResponseHeader("ETag");
      form.agent_plugins = data.temboard.plugins;
      form.cpu = data.system.cpu_count;
      const mem_gb = data.system.memory / 1024 / 1024 / 1024;
      form.mem_gb = mem_gb.toFixed(2);
      form.pg_version_summary = data.postgres.version_summary;
      form.pg_data = data.postgres.data_directory;
      form.pg_host = data.system.fqdn;
      form.pg_port = data.postgres.port;
      form.signature_status = data.signature_status;
    });
}

function open(address, port) {
  // Reset dialog state.
  error.value.clear();
  waiting.value = true;

  // Configure for target instance data.
  agent_address = address;
  agent_port = port;

  $(root.value.$el).modal("show");

  fetch_current_data().done(() => {
    // Discover may fail if agent is down.
    discover_agent().complete(() => {
      nextTick(formCmp.value.setup_multiselects);
      waiting.value = false;
    });
  });
}

function fetch_current_data() {
  return $.ajax({
    url: ["/json/settings/instance", agent_address, agent_port].join("/"),
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done((data) => {
      form.notify = data.notify;
      form.comment = data.comment;
      form.agent_key = data.agent_key;
      // Will be overriden by discover, if agent is up.
      form.pg_host = data.hostname;
      form.pg_port = data.pg_port;
      form.server_groups = data.server_groups;
      form.server_plugins = data.server_plugins;
      form.current_plugins = data.plugins;
      form.current_groups = data.groups;
    });
}

function update(data) {
  waiting.value = true;
  if (discover_data.signature_status === "valid") {
    // Ensure agent key is dropped for new agents.
    data.agent_key = null;
  }

  $.ajax({
    url: ["/json/settings/instance", agent_address, agent_port].join("/"),
    method: "POST",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({
      ...data,
      new_agent_address: agent_address,
      new_agent_port: agent_port,
      discover: discover_data,
      discover_etag,
    }),
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done(() => {
      window.location.reload();
    });
}

function reset() {
  Object.assign(form, initialForm);
  formCmp.value.teardown_multiselects();
}

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalUpdateInstance" title="Update Instance" v-on:closed="reset" ref="root">
    <InstanceForm
      ref="formCmp"
      submit_text="Update"
      v-bind:pg_host="form.pg_host"
      v-bind:pg_port="form.pg_port"
      v-bind:pg_data="form.pg_data"
      v-bind:pg_version_summary="form.pg_version_summary"
      v-bind:cpu="form.cpu"
      v-bind:mem_gb="form.mem_gb"
      v-bind:signature_status="form.signature_status"
      v-bind:groups="groups"
      v-bind:plugins="plugins"
      v-bind:notify="form.notify"
      v-bind:comment="form.comment"
      v-bind:agent_key="form.agent_key"
      v-bind:waiting="waiting"
      v-on:submit="update"
    >
      <Error ref="error"></Error>
    </InstanceForm>
  </ModalDialog>
</template>
