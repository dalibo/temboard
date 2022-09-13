<script type="text/javascript">
/** A Bootstrap dialog with two steps: discover and register.
  *
  * Supports temBoard 7.X agent with key. Discover before registration to
  * render a preview of the managed instance. Disables plugins not loaded in
  * agent.
  */

import InstanceForm from './InstanceForm.vue'
import ModalDialog from './ModalDialog.vue'

export default {
  components: {
    'instance-form': InstanceForm,
    'modal-dialog': ModalDialog
  },
  data() { return {
    // Wizard state.
    wizard_step: "discover",     //  discover, register
    error: null,
    waiting: false,

    // Form model.
    agent_address: null,
    agent_port: null,
    agent_key: "",
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
    signature_status: null
  }},
  computed: {
    groups() {
      return Array.from(this.server_groups, group => {
        return {
          name: group.name,
          disabled: false,
          selected: false
        }
      });
    },
    plugins() {
      return Array.from(this.server_plugins, name => {
        return {
          name,
          disabled: this.discover_data.temboard.plugins.indexOf(name) === -1,
          selected: this.discover_data.temboard.plugins.indexOf(name) !== -1
        }
      });
    }
  },
  updated() {
    $('[data-toggle="tooltip"]', this.$el).tooltip();
    if ('register' === this.wizard_step && this.plugins && !$("#selectGroups").data('multiselect')) {
      this.$nextTick(this.$refs.form.setup_multiselects);
    }
    if ('register' === this.wizard_step && $("#selectGroups").data('multiselect')) {
      $("#selectGroups").multiselect(this.waiting ? 'disable' : 'enable');
      $("#selectPlugins").multiselect(this.waiting ? 'disable' : 'enable');
    }
  },
  methods: {
    format_xhr_error(xhr) {
      if (0 === xhr.status) {
        return "Failed to contact server."
      }
      else if (xhr.getResponseHeader('content-type').includes('application/json')) {
          return JSON.parse(xhr.responseText).error;
        }
        else if ('text/plain' == xhr.getResponseHeader('content-type')) {
          return `<pre>${xhr.responseText}</pre>`;
        }
        else {
          return 'Unknown error. Please contact temBoard administrator.'
        }
    },
    discover() {
      this.error = null;
      this.waiting = true;
      $.ajax({
        url: ['/json/discover/instance', this.agent_address, this.agent_port].join('/'),
        type: 'get',
        contentType: "application/json",
        dataType: "json"
      }).fail(xhr => {
        this.waiting = false;
        this.error = this.format_xhr_error(xhr);
      }).done((data, _, xhr) => {
        if ('invalid' == data.signature_status) {
          this.error = `
            <p><strong>Signature missmatch !</strong></p>

            <p>Agent is not configured for this UI. You must accept
            <strong>this</strong> UI signing key in agent configuration. See
            installation documentation.</p>
          `;
          this.waiting = false;
          return;
        }

        this.discover_data = data;
        this.discover_etag = xhr.getResponseHeader('ETag')
        this.cpu = data.system.cpu_count
        var mem_gb = data.system.memory / 1024 / 1024 / 1024
        this.mem_gb = mem_gb.toFixed(2);
        this.pg_version_summary = data.postgres.version_summary
        this.pg_data = data.postgres.data_directory
        this.pg_host = data.system.fqdn
        this.pg_port = data.postgres.port
        this.signature_status = data.signature_status;

        $.ajax({
          url: '/json/settings/all/group/instance',
        }).fail(xhr => {
          this.waiting = false;
          this.error = this.format_xhr_error(xhr);
        }).done((data) => {
          this.server_groups = data.groups;
          this.server_plugins = data.loaded_plugins;
          this.waiting = false;
          this.wizard_step = "register";
        });
      });
    },
    register(data) {
      this.waiting = true;
      $.ajax({
        url: '/json/settings/instance',
        method: 'POST',
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify({
          ...data,
          new_agent_address: this.agent_address,
          new_agent_port: this.agent_port,
          discover: this.discover_data,
          discover_etag: this.discover_etag
        }),
      }).fail(xhr => {
        this.waiting = false;
        this.error = this.format_xhr_error(xhr)
      }).done(() => {
        window.location.reload();
      });
    },
    reset() {
      Object.assign(this.$data, this.$options.data());
      this.$refs.form.teardown_multiselects();
    }
  }
}
</script>

<template>
  <modal-dialog id="modalNewInstance" title="Register New Instance" v-on:closed="reset">

    <!-- Discover -->
    <div v-if="wizard_step == 'discover'">
      <form v-on:submit.prevent="discover">
        <div class="modal-body" v-if="wizard_step == 'discover'">

          <p class="alert alert-info">temBoard requires an agent to manage
          a PostgreSQL instance. Follow documentation to setup the agent
          next to your PostgreSQL instance. Set here agent address and
          port, not PostgreSQL.</p>

          <div class="alert alert-danger" v-if="error"><div v-html="error"></div></div>
          <div class="row">
            <div class="form-group col-sm-6">
              <label for="inputAgentAddress" class="control-label">Agent address</label>
              <input v-bind:disabled="waiting" id="inputAgentAddress" type="text" v-model.lazy.trim="agent_address" class="form-control" placeholder="ex: db.entreprise.lan" />
            </div>
            <div class="form-group col-sm-6">
              <label for="inputAgentPort" class="control-label">Agent port</label>
              <input v-bind:disabled="waiting" id="inputAgentPort" type="text" v-model.lazy.number.trim="agent_port" class="form-control" placeholder="ex: 2345" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>
          <button id="buttonDiscover"
                  class="btn btn-success ml-auto"
                  type="submit"
                  v-bind:disabled="waiting">
            Discover <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
          </button>
        </div>
      </form>
    </div>

    <!-- Register -->
    <div v-if="wizard_step == 'register'">
      <instance-form
        ref="form"
        submit_text="Register"
        v-bind:error="error"
        v-bind:pg_host="pg_host"
        v-bind:pg_port="pg_port"
        v-bind:pg_data="pg_data"
        v-bind:pg_version_summary="pg_version_summary"
        v-bind:cpu="cpu"
        v-bind:mem_gb="mem_gb"
        v-bind:signature_status="signature_status"
        v-bind:groups="groups"
        v-bind:plugins="plugins"
        v-bind:notify="notify"
        v-bind:comment="comment"
        v-bind:agent_key="agent_key"
        v-bind:waiting="waiting"
        v-on:submit="register"
        />
    </div>

  </modal-dialog>
</template>
