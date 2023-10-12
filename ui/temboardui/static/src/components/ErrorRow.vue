<script type="text/javascript">
// A Bootstrap grid row showing a global page error.

import Error from "./Error.vue";

export default {
  components: {
    error: Error,
  },
  methods: {
    clear: function () {
      this.$refs.error.clear();
    },
    fromXHR: function (xhr) {
      this.$refs.error.fromXHR(xhr);
    },
  },
};
</script>

<template>
  <div class="row justify-content-center" v-cloak>
    <div class="col col-xl-6 col-10">
      <error ref="error"></error>
    </div>
  </div>
</template>
