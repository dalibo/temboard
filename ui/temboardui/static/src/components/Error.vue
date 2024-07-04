<script setup>
// A Bootstrap error alert.
import { ref } from "vue";

const code = ref(null);
const error = ref(null);

const props = defineProps({
  showTitle: { default: true },
});

function clear() {
  error.value = null;
  code.value = null;
}

function fromXHR(xhr) {
  if (0 === xhr.status) {
    code.value = null;
    error.value = "Failed to contact temBoard server.";
  } else {
    code.value = xhr.status;
    const contentType = xhr.getResponseHeader("content-type");
    if (contentType.includes("application/json")) {
      error.value = JSON.parse(xhr.responseText).error;
      if (error.value === "") {
        error.value = "Unknown error. Please contact temBoard administrator.";
      }
    } else if (contentType.includes("text/plain")) {
      error.value = `<pre>${xhr.responseText}</pre>`;
    } else {
      error.value = "Unknown error. Please contact temBoard administrator.";
    }
  }
}
function setHTML(html) {
  code.value = null;
  error.value = html;
}

defineExpose({ clear, fromXHR, setHTML });
</script>

<template>
  <div class="alert alert-danger alert-dismissible" role="alert" v-if="error" v-cloak>
    <h4 class="modal-title" id="ErrorLabel">
      <template v-if="showTitle">Error {{ code }}</template>
    </h4>
    <button type="button" class="btn-close" aria-label="Close" @click.prevent="clear"></button>

    <div class="pe-3">
      <p v-html="error"></p>
    </div>
  </div>
</template>
