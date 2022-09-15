<script type="text/javascript">
  /**
    * A Bootstrap dialog editing instance properties.
    *
    * Supports temBoard 7.X agent with key. Discover before registration to
    * render a preview of the managed instance. Disables plugins not loaded in
    * agent.
    */

  import Error from '../Error.vue'
  import ModalDialog from '../ModalDialog.vue'
  import InstanceForm from './InstanceForm.vue'

  export default {
    components: {
      'error': Error,
      'instance-form': InstanceForm,
      'modal-dialog': ModalDialog
    },
    data() { return {
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
      discover_etag: null,
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
      signature_status: null
    }},
    computed: {
      plugins() {
        return Array.from(this.server_plugins, name => {
          return {
            name,
            disabled: this.agent_plugins.length > 0 && this.agent_plugins.indexOf(name) === -1,
            selected: this.current_plugins.indexOf(name) !== -1
          }
        });
      },
      groups() {
        return Array.from(this.server_groups, group => { return {
          name: group.name,
          selected: this.current_groups.indexOf(group.name) !== -1
        }});
      }
    },
    updated() {
      $('[data-toggle="tooltip"]', this.$el).tooltip();
      if ($("#selectGroups").data('multiselect')) {
        $("#selectGroups").multiselect(this.waiting ? 'disable' : 'enable');
        $("#selectPlugins").multiselect(this.waiting ? 'disable' : 'enable');
      }
    },
    methods: {
      discover_agent() {
        return $.ajax({
          url: ['/json/discover/instance', this.agent_address, this.agent_port].join('/'),
          type: 'get',
          contentType: "application/json",
          dataType: "json"
        }).fail(xhr => {
          this.waiting = false;
          this.$refs.error.fromXHR(xhr)
        }).done((data, _, xhr) => {
          if ('invalid' == data.signature_status) {
            this.$refs.error.setHTML(`
              <p><strong>Signature missmatch !</strong></p>

              <p>Agent is not configured for this UI. You must accept
              <strong>this</strong> UI signing key in agent configuration. See
              installation documentation.</p>
            `)
            this.waiting = false;
            return;
          }

          this.discover_data = data;
          this.discover_etag = xhr.getResponseHeader('ETag')
          this.agent_plugins = data.temboard.plugins;
          this.cpu = data.system.cpu_count;
          var mem_gb = data.system.memory / 1024 / 1024 / 1024;
          this.mem_gb = mem_gb.toFixed(2);
          this.pg_version_summary = data.postgres.version_summary;
          this.pg_data = data.postgres.data_directory;
          this.pg_host = data.system.fqdn;
          this.pg_port = data.postgres.port;
          this.signature_status = data.signature_status;
        });
      },
      open(agent_address, agent_port) {
        // Reset dialog state.
        this.$refs.error.clear()
        this.waiting = true;

        // Configure for target instance data.
        this.agent_address = agent_address;
        this.agent_port = agent_port;

        $(this.$el).modal('show');

        this.fetch_current_data().done(() => {
          this.$nextTick(this.$refs.form.setup_multiselects);
          // Discover may fail if agent is down.
          this.discover_agent().done(() => {
            this.waiting = false;
          });
        });
      },
      fetch_current_data() {
        return $.ajax({
          url: ['/json/settings/instance', this.agent_address, this.agent_port].join('/')
        }).fail(xhr => {
          this.waiting = false;
          this.$refs.error.fromXHR(xhr)
        }).done(data => {
          this.notify = data.notify;
          this.comment = data.comment;
          this.agent_key = data.agent_key;
          // Will be overriden by discover, if agent is up.
          this.pg_host = data.hostname;
          this.pg_port = data.pg_port;
          this.server_groups = data.server_groups;
          this.server_plugins = data.server_plugins;
          this.current_data = data;
          this.current_plugins = data.plugins;
          this.current_groups = data.groups;
        });
      },
      update(data) {
        this.waiting = true;
        $.ajax({
          url: ['/json/settings/instance', this.agent_address, this.agent_port].join('/'),
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
          this.$refs.error.fromXHR(xhr)
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
  <modal-dialog id="modalUpdateInstance" title="Update Instance" v-on:closed="reset">
    <instance-form
      ref="form"
      submit_text="Update"
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
      v-on:submit="update"
      >
      <error ref="error"></error>
    </instance-form>
  </modal-dialog>
</template>
