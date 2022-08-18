/* eslint-env es6 */
/* global instances, Vue, VueRouter, Dygraph, moment, _, getParameterByName */
$(function() { Vue.component('new-instance-wizard', {    /*
    * A Bootstrap dialog with two steps: discover and register.
    *
    * Supports temBoard 7.X agent with key. Discover before registration to
    * render a preview of the managed instance. Disables plugins not loaded in
    * agent.
    */
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
    mem_gb: null,
    pg_data: null,
    pg_host: null,
    pg_port: null,
    pg_version_summary: null,
    ui_groups: null,
    ui_plugins: [],
    signature_status: null
  }},
  computed: {
    groups() {
      return Array.from(this.ui_groups, group => {
        return {
          name: group.name,
          disabled: false,
          selected: false
        }
      });
    },
    plugins() {
      return Array.from(this.ui_plugins, name => {
        return {
          name,
          disabled: this.discover_data.plugins.indexOf(name) === -1,
          selected: this.discover_data.plugins.indexOf(name) !== -1
        }
      });
    }
  },
  mounted() {
    // Reset component state on Bootstrap hidden event.
    $(this.$el).on("hidden.bs.modal", this.reset);
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
    format_xhr_error: function(xhr) {
      if (xhr.getResponseHeader('content-type').includes('application/json')) {
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
      }).done(data => {
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
        this.cpu = data.cpu;
        var mem_gb = data.memory_size / 1024 / 1024 / 1024;
        this.mem_gb = mem_gb.toFixed(2);
        this.pg_version_summary = data.pg_version_summary;
        this.pg_data = data.pg_data;
        this.pg_host = data.hostname;
        this.pg_port = data.pg_port;
        this.signature_status = data.signature_status;

        $.ajax({
          url: '/json/settings/all/group/instance',
        }).fail(xhr => {
          this.waiting = false;
          this.error = this.format_xhr_error(xhr);
        }).done((data) => {
          this.ui_groups = data.groups;
          this.ui_plugins = data.loaded_plugins;
          this.waiting = false;
          this.wizard_step = "register";
        });
      });
    },
    register(data) {
      this.waiting = true;
      var data = {
        ...this.discover_data,
        ...data,
        new_agent_address: this.agent_address,
        new_agent_port: this.agent_port
      };
      $.ajax({
        url: '/json/settings/instance',
        method: 'POST',
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify(data),
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
  },
  template: `
  <div class="modal fade" id="modalNewInstance" role="dialog" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h4 class="modal-title">Register New Instance</h4>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        </div>

        <!-- Discover -->
        <div v-if="wizard_step == 'discover'">
          <form v-on:submit.prevent="discover">
            <div class="modal-body" v-if="wizard_step == 'discover'">

              <p class="alert alert-info">temBoard requires an agent to manage
              a PostgreSQL instance. Follow documentation to setup the agent
              next to your PostgreSQL instance. Set here agent address and
              port, not PostgreSQL.</p>

              <div class="row alert alert-danger" v-if="error"><div v-html="error"></div></div>
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
      </div>
    </div>
  </div>
  `
})});
