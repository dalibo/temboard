<script setup>
/**
 * A Bootstrap dialog editing instance properties.
 */
import { Modal, Tooltip } from "bootstrap";
import $ from "jquery";
import { computed, nextTick, onUpdated, reactive, ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";
import InstanceForm from "./InstanceForm.vue";

const root = ref(null);
const error = ref(null);
const formCmp = ref(null);
const waiting = ref(false);
const initialForm = {
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
  const tooltipTriggerList = root.value.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((el) => new Tooltip(el));
});

function open(address, port) {
  // Reset dialog state.
  error.value.clear();
  waiting.value = true;

  // Configure for target instance data.
  agent_address = address;
  agent_port = port;

  new Modal(root.value.$el).show();

  fetch();
}

function fetch() {
  return $.when(
    $.ajax({
      url: `/json/instances/${agent_address}/${agent_port}`,
      error: (xhr) => {
        error.value.fromXHR(xhr);
      },
      success: (data) => {
        form.notify = data.notify;
        form.comment = data.comment;
        // Will be overriden by discover, if agent is up.
        form.pg_host = data.hostname;
        form.pg_port = data.pg_port;
        form.current_plugins = data.plugins;
        form.current_groups = data.groups;
      },
    }),
    $.ajax({
      url: "/json/groups/instance",
      error: (xhr) => {
        error.value.fromXHR(xhr);
      },
      success: (data) => {
        form.server_groups = data;
      },
    }),
    $.ajax({
      url: "/json/plugins",
      error: (xhr) => {
        error.value.fromXHR(xhr);
      },
      success: (data) => {
        form.server_plugins = data;
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
  Object.assign(form, initialForm);
}

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalUpdateInstance" title="Update Instance" v-on:closed="reset" ref="root">
    <InstanceForm
      ref="formCmp"
      submit_text="Update"
      type="Update"
      :pg_host="form.pg_host"
      :pg_port="form.pg_port"
      :pg_data="form.pg_data"
      :pg_version_summary="form.pg_version_summary"
      :cpu="form.cpu"
      :mem_gb="form.mem_gb"
      :signature_status="form.signature_status"
      :groups="groups"
      :plugins="plugins"
      :notify="form.notify"
      :comment="form.comment"
      :waiting="waiting"
      v-on:submit="update"
    >
      <Error ref="error"></Error>
    </InstanceForm>
  </ModalDialog>
</template>
