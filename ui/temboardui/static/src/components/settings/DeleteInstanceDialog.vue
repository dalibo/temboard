<script setup>
// A confirm dialog
import { Modal } from "bootstrap";
import $ from "jquery";
import { ref } from "vue";

import Error from "../Error.vue";
import ModalDialog from "../ModalDialog.vue";
import InstanceDetails from "./InstanceDetails.vue";

const root = ref(null);
const error = ref(null);
const waiting = ref(false);
const pg_host = ref(null);
const pg_port = ref(null);

let agent_address = null;
let agent_port = null;

function open(address, port) {
  agent_address = address;
  agent_port = port;

  new Modal(root.value.$el).show();

  $.ajax({
    url: ["/json/settings/instance", agent_address, agent_port].join("/"),
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done((data) => {
      pg_host.value = data.hostname;
      pg_port.value = data.pg_port;
      waiting.value = false;
    });
}

function delete_() {
  waiting.value = true;
  $.ajax({
    url: "/json/settings/delete/instance",
    type: "POST",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({ agent_address, agent_port }),
  })
    .fail((xhr) => {
      waiting.value = false;
      error.value.fromXHR(xhr);
    })
    .done(() => {
      window.location.reload();
    });
}

defineExpose({ open });
</script>

<template>
  <ModalDialog id="modalDeleteInstance" title="Delete Instance" ref="root">
    <div class="modal-body">
      <Error ref="error" :showTitle="false"></Error>
      <p class="text-center">
        <strong>Please confirm the deletion of the following instance:</strong>
      </p>
      <InstanceDetails :pg_host="pg_host" :pg_port="pg_port" />
    </div>

    <div class="modal-footer">
      <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
      <button id="buttonDelete" class="btn btn-danger ms-auto" type="button" @click="delete_" :disabled="waiting">
        Yes, delete this instance
        <i v-if="waiting" class="fa fa-spinner fa-spin loader"></i>
      </button>
    </div>
  </ModalDialog>
</template>
