<script type="text/javascript">
/* A confirm dialog */

import InstanceDetails from './InstanceDetails.vue'
import ModalDialog from './ModalDialog.vue'

export default {
  components: {
    'instance-details': InstanceDetails,
    'modal-dialog': ModalDialog
  },
  data() { return {
    error: null,
    waiting: false,

    agent_address: null,
    agent_port: null,

    pg_host: null,
    pg_port: null,
    pg_data: null,
    pg_version_summary: null,
    cpu: null,
    mem_gb: null
  }},
  methods: {
    fetch_current_data() {
      return $.ajax({
        url: ['/json/settings/instance', this.agent_address, this.agent_port].join('/')
      }).fail(xhr => {
        this.waiting = false;
        this.error = this.format_xhr_error(xhr);
      }).done(data => {
        this.pg_host = data.hostname;
        this.pg_port = data.pg_port;
        this.pg_data = data.pg_data;
        this.pg_version_summary = data.pg_version_summary;
        this.cpu = data.cpu;
        var mem_gb = data.memory_size / 1024 / 1024 / 1024;
        this.mem_gb = mem_gb.toFixed(2);
      });
    },
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
    open(agent_address, agent_port) {
      this.agent_address = agent_address;
      this.agent_port = agent_port;

      $(this.$el).modal('show');

      this.fetch_current_data().done(() => {
        this.waiting = false;
      });
    },
    delete_() {
      this.waiting = true;
      $.ajax({
        url: '/json/settings/delete/instance',
        type: 'POST',
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify({agent_address: this.agent_address, agent_port: this.agent_port})
      }).fail(xhr => {
        this.waiting = false;
        this.error = this.format_xhr_error(xhr);
      }).done(() => {
        window.location.reload();
      });
    }
  }
}
</script>

<template>
  <modal-dialog id="modalDeleteInstance" title="Delete Instance">
    <div class="modal-body">
      <div class="alert alert-danger" v-if="error"><div v-html="error"></div></div>
      <p class="text-center"><strong>Please confirm the deletion of the following instance:</strong></p>
      <instance-details
        v-bind:pg_host="pg_host"
        v-bind:pg_port="pg_port"
        v-bind:pg_version_summary="pg_version_summary"
        v-bind:pg_data="pg_data"
        v-bind:cpu="cpu"
        v-bind:mem_gb="mem_gb"
        />
    </div>

    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>
      <button id="buttonDelete"
              class="btn btn-danger ml-auto"
              type="button"
              @click="delete_"
              v-bind:disabled="waiting">
        Yes, delete this instance <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </modal-dialog>
</template>
