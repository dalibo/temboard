<script setup>
// A Bootstrap grid row showing a global page error.
import { ref } from "vue";

import Error from "./Error.vue";

const error = ref(null);

function clear() {
  error.value.clear();
}
function fromXHR(xhr) {
  error.value.fromXHR(xhr);
}
defineExpose({ clear, fromXHR });
</script>

<template>
  <div class="row justify-content-center" v-cloak>
    <div class="col col-xl-6 col-10">
      <Error ref="error"></Error>
    </div>
  </div>
</template>
