<script setup>
/**
 * A Bootstrap dialog editing instance properties.
 */
import { Tooltip } from "bootstrap";
import $ from "jquery";
import { computed, nextTick, onUpdated, reactive, ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";
import InstanceForm from "./InstanceForm.vue";

function open(address, port) {
  reset();

  // Configure for target instance data.
  agent_address = address;
  agent_port = port;
  root.value.show();
}

defineExpose({ open });

const root = ref(null);
const error = ref(null);
const waiting = ref(true);
const failing = ref(false);
const disabled = computed(() => waiting.value || failing.value);
const initialModel = {
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
const model = reactive({ ...initialModel });
let agent_address = null;
let agent_port = null;
let discover_data;
let discover_etag;

const plugins = computed(() => {
  return Array.from(model.server_plugins, (name) => {
    return {
      name,
      disabled: model.agent_plugins.length > 0 && model.agent_plugins.indexOf(name) === -1,
      selected: model.current_plugins.indexOf(name) !== -1,
    };
  });
});

const groups = computed(() => {
  return Array.from(model.server_groups, (group) => {
    return {
      name: group.name,
      selected: model.current_groups.indexOf(group.name) !== -1,
    };
  });
});

onUpdated(() => {
  const tooltipTriggerList = root.value.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((el) => new Tooltip(el));
});

function fetch() {
  return $.when(
    $.ajax({
      url: `/json/instances/${agent_address}/${agent_port}`,
      error: (xhr) => {
        error.value.fromXHR(xhr);
        failing.value = true;
      },
      success: (data) => {
        model.notify = data.notify;
        model.comment = data.comment;
        // Will be overriden by discover, if agent is up.
        model.pg_host = data.hostname;
        model.pg_port = data.pg_port;
        model.current_plugins = data.plugins;
        model.current_groups = data.groups;
      },
    }),
    $.ajax({
      url: "/json/groups/instance",
      error: (xhr) => {
        error.value.fromXHR(xhr);
      },
      success: (data) => {
        model.server_groups = data;
      },
    }),
    $.ajax({
      url: "/json/plugins",
      error: (xhr) => {
        error.value.fromXHR(xhr);
      },
      success: (data) => {
        model.server_plugins = data;
      },
    }),
    discover(),
  ).always(() => {
    waiting.value = false;
  });
}

function discover() {
  return $.ajax({
    url: `/json/instances/${agent_address}/${agent_port}/discover`,
    type: "get",
    contentType: "application/json",
    dataType: "json",
  })
    .fail((xhr) => {
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
        return;
      }

      discover_data = data;
      discover_etag = xhr.getResponseHeader("ETag");
      model.agent_plugins = data.temboard.plugins;
      model.cpu = data.system.cpu_count;
      const mem_gb = data.system.memory / 1024 / 1024 / 1024;
      model.mem_gb = mem_gb.toFixed(2);
      model.pg_version_summary = data.postgres.version_summary;
      model.pg_data = data.postgres.data_directory;
      model.pg_host = data.system.fqdn;
      model.pg_port = data.postgres.port;
      model.signature_status = data.signature_status;
    });
}

function update(data) {
  waiting.value = true;

  $.ajax({
    url: `/json/instances/${agent_address}/${agent_port}`,
    method: "PUT",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({
      ...data,
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
  Object.assign(model, initialModel);
  error.value.clear();
  waiting.value = true;
}
</script>

<template>
  <ModalDialog ref="root" title="Update Instance" v-on:closed="reset">
    <InstanceForm
      submit_text="Update"
      type="Update"
      :pg_host="model.pg_host"
      :pg_port="model.pg_port"
      :pg_data="model.pg_data"
      :pg_version_summary="model.pg_version_summary"
      :cpu="model.cpu"
      :mem_gb="model.mem_gb"
      :signature_status="model.signature_status"
      :groups="groups"
      :plugins="plugins"
      :notify="model.notify"
      :comment="model.comment"
      :waiting="waiting"
      :disabled="disabled"
      v-on:submit="update"
    >
      <Error ref="error"></Error>
    </InstanceForm>
  </ModalDialog>
</template>
