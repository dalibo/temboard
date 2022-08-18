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
    groups: null,
    mem_gb: null,
    pg_data: null,
    pg_host: null,
    pg_port: null,
    pg_version_summary: null,
    ui_plugins: [],
    signature_status: null
  }},
  computed: {
    agent_plugins() {
      return Array.from(this.ui_plugins, name => {
        return {
          name,
          disabled: this.discover_data.plugins.indexOf(name) === -1
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
    discover: function() {
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
          this.groups = data.groups;
          this.ui_plugins = data.loaded_plugins;
          this.waiting = false;
          this.wizard_step = "register";
          this.$nextTick(() => {
            var options = {
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
                `
              },
              numberDisplayed: 1
            };
            $("#selectGroups").multiselect(options);
            $("#selectPlugins").multiselect(options);
          });
        });

      });
    },
    register: function() {
      this.waiting = true;
      var data = {
        ...this.discover_data,
        new_agent_address: this.agent_address,
        new_agent_port: this.agent_port,
        agent_key: this.agent_key,
        groups: $("#selectGroups").val(),
        plugins: $("#selectPlugins").val(),
        notify: this.notify,
        comment: this.comment
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
    reset: function() {
      Object.assign(this.$data, this.$options.data());
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
        <form v-on:submit.prevent="discover" v-if="wizard_step == 'discover'">
          <div class="modal-body">

            <p class="alert alert-info">temBoard requires an agent to manage
            a PostgreSQL instance. Follow documentation to setup the agent
            next to your PostgreSQL instance. Set here agent address and
            port, not PostgreSQL.</p>

            <div class="row" class="alert alert-danger" v-if="error"><div v-html="error"></div></div>
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

        <!-- Register -->
        <form v-on:submit.prevent="register" v-if="wizard_step == 'register'">
          <div class="modal-body p-3">
            <div class="row">
              <div class="alert alert-light mx-auto pa-6">
                <h2 class="text-center"><span v-html="pg_host"/>:<span v-html="pg_port"/></h2>
                <p class="text-center">
                  <span v-html="cpu"/> CPU - <span v-html="mem_gb"/> GB memory<br/>
                  <strong><span v-html="pg_version_summary"/> serving <span v-html="pg_data"/>.</strong><br/>
                </p>
              </div>
            </div>
            <div class="row" class="alert alert-danger" v-if="error"><div v-html="error"></div></div>
            <div class="row" v-if="signature_status === undefined">
              <!-- Ask for legacy agent key. -->
              <div class="form-group col-sm-12">
                <label for="inputAgentKey" class="control-label">
                  Agent secret key
                  <i id="agent-key-deprecation-tooltip"
                      class="fa fa-info-circle text-muted" data-toggle="tooltip"
                      title="Using agent secret key is deprecated. You should upgrade agent to version 8.">
                  </i>
                </label>
                <input id="inputAgentKey"
                        class="form-control"
                        placeholder="Find it in agent configuration file."
                        required
                        v-model="agent_key"
                        v-bind:disabled="waiting" />
              </div>
            </div>
            <div class="row">
              <div id="divGroups" class="form-group col-sm-6">
                <label for="selectGroups">Groups</label>
                <select id="selectGroups" v-bind:disabled="waiting" multiple required>
                  <option v-for="group of groups"
                          v-bind:key="group.name"
                          v-bind:value="group.name">{{ group.name }}</option>
                </select>
                <div id="tooltip-container"></div>
              </div>
              <div id="divPlugins" class="form-group col-sm-6">
                <label for="selectPlugins" class="control-label">Plugins</label>
                <select id="selectPlugins" v-bind:disabled="waiting" multiple="multiple">
                  <option v-for="plugin of agent_plugins"
                          v-bind:key="plugin.name"
                          v-bind:value="plugin.name"
                          v-bind:selected="!plugin.disabled"
                          v-bind:disabled="plugin.disabled ? 'disabled' : null"
                          v-bind:class="plugin.disabled ? 'disabled' : null"
                          v-bind:title="plugin.disabled ? 'Plugin disabled by agent.' : null">{{ plugin.name }}</option>
                </select>
              </div>
            </div>
            <div class="row">
              <div class="col-sm-12">
                <div class="form-check">
                  <input id="inputNotify"
                          class="form-check-input"
                          type="checkbox"
                          v-model="notify"
                          v-bind:disabled="waiting" />
                  <label for="inputNotify" class="control-label">Notify users of any status alert.</label>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="form-group col-sm-12">
                <label for="inputComment" class="control-label">Comment</label>
                <textarea id="inputComment"
                          class="form-control"
                          rows="3"
                          v-model="comment"
                          v-bind:disabled="waiting">
                </textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>
            <button id="buttonRegister"
                    class="btn btn-success ml-auto"
                    type="submit"
                    v-bind:disabled="waiting">
              Register <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
  `
})});
