/* eslint-env es6 */
/* global instances, Vue, VueRouter, Dygraph, moment, _, getParameterByName */
$(function() { Vue.component('instance-form', {    /*
    * An HTML form editing instance properties.
    *
    * This form has only presentation logic, no I/O.
    */
  props: [
    'submit_text',  // Submit button label.
    'waiting',  // Whether parent is interacting with server.
    'error',

    // Discover readonly data.
    'pg_host',
    'pg_port',
    'pg_data',
    'pg_version_summary',
    'cpu',
    'mem_gb',
    'signature_status',

    // Agent configuration
    'agent_key',
    'comment',
    'notify',
    'groups',
    'plugins'
  ],
  updated() {
    $('[data-toggle="tooltip"]', this.$el).tooltip();
    if ($("#selectGroups").data('multiselect')) {
      $("#selectGroups").multiselect(this.waiting ? 'disable' : 'enable');
      $("#selectPlugins").multiselect(this.waiting ? 'disable' : 'enable');
    }
  },
  methods: {
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
    submit() {
      // data generates payload for both POST /json/settings/instances and POST
      // /json/settings/instances/X.X.X.X/PPPP.
      var data = {
        // Define paramters.
        new_agent_address: this.agent_address,
        new_agent_port: this.agent_port,
        agent_key: this.agent_key,
        groups: $("#selectGroups").val(),
        plugins: $("#selectPlugins").val(),
        notify: this.notify,
        comment: this.comment
      };
      this.$emit('submit', data);
    }
  },
  template: `
  <form v-on:submit.prevent="submit">
    <div class="modal-body p-3">
      <div class="row alert alert-danger" v-if="error"><div v-html="error"></div></div>

      <div class="row">
        <div class="alert alert-light mx-auto pa-6">
          <h2 class="text-center"><span v-html="pg_host"/>:<span v-html="pg_port"/></h2>
          <p class="text-center">
            <span v-html="cpu"/> CPU - <span v-html="mem_gb"/> GB memory<br/>
            <strong><span v-html="pg_version_summary"/> serving <span v-html="pg_data"/>.</strong><br/>
          </p>
        </div>
      </div>
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
                    v-bind:selected="group.selected ? 'selected' : null"
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
                    v-bind:class="{ disabled: plugin.disabled }"
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
      <button id="buttonSubmit"
              class="btn btn-success ml-auto"
              type="submit"
              v-bind:disabled="waiting">
        {{ submit_text }} <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </form>
  `
})});
