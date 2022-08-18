/* eslint-env es6 */
/* global instances, Vue, VueRouter, Dygraph, moment, _, getParameterByName */
$(function() { Vue.component('update-instance-dialog', {    /*
    * A Bootstrap dialog editing instance properties.
    *
    * Supports temBoard 7.X agent with key. Discover before registration to
    * render a preview of the managed instance. Disables plugins not loaded in
    * agent.
    */
  data() { return {
    error: null,
    waiting: false,

    agent_address: null,
    agent_port: null,

    // Form model.
    agent_key: "",
    comment: "",
    notify: true,

    // Instance information from API.
    current_data: null,
    discover_data: null,
    cpu: null,
    ui_groups: [],
    current_groups: [],
    mem_gb: null,
    pg_data: null,
    pg_host: null,
    pg_port: null,
    pg_version_summary: null,
    ui_plugins: [],
    current_plugins: [],
    agent_plugins: [],
    signature_status: null
  }},
  computed: {
    plugins() {
      return Array.from(this.ui_plugins, name => {
        return {
          name,
          disabled: this.agent_plugins.indexOf(name) === -1,
          selected: this.current_plugins.indexOf(name) !== -1
        }
      });
    },
    groups() {
      return Array.from(this.ui_groups, group => { return {
        name: group.name,
        selected: this.current_groups.indexOf(group.name) !== -1
      }});
    }
  },
  mounted() {
    // Reset component state on Bootstrap hidden event.
    $(this.$el).on("hidden.bs.modal", this.reset);
  },
  updated() {
    $('[data-toggle="tooltip"]', this.$el).tooltip();
    if ($("#selectGroups").data('multiselect')) {
      $("#selectGroups").multiselect(this.waiting ? 'disable' : 'enable');
      $("#selectPlugins").multiselect(this.waiting ? 'disable' : 'enable');
    }
  },
  methods: {
    format_xhr_error(xhr) {
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
    discover_agent() {
      return $.ajax({
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
        this.agent_plugins = data.plugins;
      });
    },
    open(agent_address, agent_port) {
      // Reset dialog state.
      this.error = null;
      this.waiting = true;

      // Configure for target instance data.
      this.agent_address = agent_address;
      this.agent_port = agent_port;

      $(this.$el).modal('show');

      this.discover_agent().done(() => {
        this.fetch_current_data().done(() => {
          this.waiting = false;
          this.$nextTick(this.setup_multiselects);
        });
      });
    },
    fetch_current_data() {
      return $.ajax({
        url: ['/json/settings/instance', this.agent_address, this.agent_port].join('/')
      }).fail(xhr => {
        this.waiting = false;
        this.error = this.format_xhr_error(xhr);
      }).done(data => {
        this.notify = data.notify;
        this.comment = data.comment;
        this.agent_key = data.agent_key;
        this.ui_groups = data.groups;
        this.ui_plugins = data.loaded_plugins;
        this.current_data = data;
        this.current_plugins = data.enabled_plugins;
        this.current_groups = data.in_groups;
      });
    },
    setup_multiselects() {
      // jQuery multiselect plugin must be called once Vue template is rendered.
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
    },
    update: function() {
      this.waiting = true;
      var data = {
        // Update discover data.
        ...this.discover_data,
        // The new_* attributes are actually totaly useless. Server uses only
        // the URL parameter. However, these attributes are still validated
        // using the same validator as instance registration.
        new_agent_address: this.agent_address,
        new_agent_port: this.agent_port,
        // Effective new parameters of the instances.
        agent_key: this.agent_key,
        groups: $("#selectGroups").val(),
        plugins: $("#selectPlugins").val(),
        notify: this.notify,
        comment: this.comment
      };
      $.ajax({
        url: ['/json/settings/instance', this.agent_address, this.agent_port].join('/'),
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
  <div class="modal fade" id="modalUpdateInstance" role="dialog" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h4 class="modal-title">Update Instance</h4>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        </div>

        <form v-on:submit.prevent="update">
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
                  <i id="cpu-info"
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
                          v-bind:selected="group.selected ? 'selecte' : null"
                          v-bind:value="group.name">{{ group.name }}</option>
                </select>
                <div id="tooltip-container"></div>
              </div>
              <div id="divPlugins" class="form-group col-sm-6">
                <label for="selectPlugins" class="control-label">Plugins</label>
                <select id="selectPlugins" v-bind:disabled="waiting" multiple="multiple">
                  <option v-for="plugin of plugins"
                          v-bind:key="plugin.name"
                          v-bind:value="plugin.name"
                          v-bind:selected="plugin.selected"
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
            <button id="buttonUpdate"
                    class="btn btn-success ml-auto"
                    type="submit"
                    v-bind:disabled="waiting">
              Update <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
  `
})});
