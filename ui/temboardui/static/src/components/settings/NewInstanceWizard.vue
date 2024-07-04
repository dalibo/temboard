<script setup>
/* A Bootstrap dialog with two steps: discover and register.
 *
 * Supports temBoard 7.X agent with key. Discover before registration to
 * render a preview of the managed instance. Disables plugins not loaded in
 * agent.
 */
import $ from "jquery";
import { computed, nextTick, onUpdated, reactive, ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";
import InstanceForm from "./InstanceForm.vue";

const root = ref(null);
const error = ref(null);
const formCmp = ref(null);
const waiting = ref(false);

const initialState = {
  // Wizard state.
  wizard_step: "discover",

  // Form model.
  agent_address: null,
  agent_port: null,
  comment: "",
  notify: true,

  // Instance information from API.
  cpu: null,
  discover_data: null,
  discover_etag: null,
  mem_gb: null,
  pg_data: null,
  pg_host: null,
  pg_port: null,
  pg_version_summary: null,
  server_groups: [],
  server_plugins: [],
  signature_status: null,
};
const state = reactive({ ...initialState });

const groups = computed(() => {
  return Array.from(state.server_groups, (group) => {
    return {
      name: group.name,
      disabled: false,
      selected: false,
    };
  });
});

const plugins = computed(() => {
  return Array.from(state.server_plugins, (name) => {
    return {
      name,
      disabled: state.discover_data.temboard.plugins.indexOf(name) === -1,
      selected: state.discover_data.temboard.plugins.indexOf(name) !== -1,
    };
  });
});

onUpdated(() => {
  $('[data-bs-toggle="tooltip"]', root.value.$el).tooltip();
});

function discover() {
  waiting.value = true;
  $.ajax({
    url: ["/json/discover/instance", state.agent_address, state.agent_port].join("/"),
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

      state.discover_data = data;
      state.discover_etag = xhr.getResponseHeader("ETag");
      state.cpu = data.system.cpu_count;
      var mem_gb = data.system.memory / 1024 / 1024 / 1024;
      state.mem_gb = mem_gb.toFixed(2);
      state.pg_version_summary = data.postgres.version_summary;
      state.pg_data = data.postgres.data_directory;
      state.pg_host = data.system.fqdn;
      state.pg_port = data.postgres.port;
      state.signature_status = data.signature_status;

      $.ajax({
        url: "/json/settings/all/group/instance",
      })
        .fail((xhr) => {
          waiting.value = false;
          error.value.fromXHR(xhr);
        })
        .done((data) => {
          state.server_groups = data.groups;
          state.server_plugins = data.loaded_plugins;
          waiting.value = false;
          state.wizard_step = "register";
        });
    });
}

function register(data) {
  waiting.value = true;
  $.ajax({
    url: "/json/settings/instance",
    method: "POST",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({
      ...data,
      new_agent_address: state.agent_address,
      new_agent_port: state.agent_port,
      discover: state.discover_data,
      discover_etag: state.discover_etag,
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
  Object.assign(state, initialState);
}
</script>

<template>
  <ModalDialog id="modalNewInstance" title="Register New Instance" v-on:closed="reset" ref="root">
    <!-- Discover -->
    <div v-if="state.wizard_step == 'discover'" v-cloak>
      <form v-on:submit.prevent="discover">
        <div class="modal-body">
          <p class="alert alert-info">
            temBoard requires an agent to manage a PostgreSQL instance. Follow documentation to setup the agent next to
            your PostgreSQL instance. Set here agent address and port, not PostgreSQL.
          </p>

          <Error ref="error" :showTitle="false"></Error>

          <div class="row">
            <div class="form-group col-sm-6">
              <label for="inputAgentAddress" class="form-label">Agent address</label>
              <input
                :disabled="waiting"
                id="inputAgentAddress"
                type="text"
                v-model.lazy.trim="state.agent_address"
                class="form-control"
                placeholder="ex: db.entreprise.lan"
              />
            </div>
            <div class="form-group col-sm-6">
              <label for="inputAgentPort" class="form-label">Agent port</label>
              <input
                :disabled="waiting"
                id="inputAgentPort"
                type="text"
                v-model.lazy.number.trim="state.agent_port"
                class="form-control"
                placeholder="ex: 2345"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
          <button id="buttonDiscover" class="btn btn-success ms-auto" type="submit" :disabled="waiting">
            Discover
            <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
          </button>
        </div>
      </form>
    </div>

    <!-- Register -->
    <div v-if="state.wizard_step == 'register'" v-cloak>
      <InstanceForm
        ref="formCmp"
        submit_text="Register"
        type="New"
        :pg_host="state.pg_host"
        :pg_port="state.pg_port"
        :pg_data="state.pg_data"
        :pg_version_summary="state.pg_version_summary"
        :cpu="state.cpu"
        :mem_gb="state.mem_gb"
        :signature_status="state.signature_status"
        :groups="groups"
        :plugins="plugins"
        :notify="state.notify"
        :comment="state.comment"
        :waiting="waiting"
        v-on:submit="register"
      >
        <Error ref="error" :showTitle="false"></Error>
      </InstanceForm>
    </div>
  </ModalDialog>
</template>
