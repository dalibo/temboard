<script type="text/javascript">
// A Bootstrap error alert.

export default {
  data: function () {
    return {
      code: null,
      error: null,
    };
  },
  props: {
    showTitle: { default: true },
  },
  methods: {
    clear: function () {
      this.error = null;
      this.code = null;
    },
    fromXHR: function (xhr) {
      if (0 === xhr.status) {
        this.code = null;
        this.error = "Failed to contact temBoard server.";
      } else {
        this.code = xhr.status;
        var contentType = xhr.getResponseHeader("content-type");
        if (contentType.includes("application/json")) {
          this.error = JSON.parse(xhr.responseText).error;
          if (this.error === "") {
            this.error = "Unknown error. Please contact temBoard administrator.";
          }
        } else if (contentType.includes("text/plain")) {
          this.error = `<pre>${xhr.responseText}</pre>`;
        } else {
          this.error = "Unknown error. Please contact temBoard administrator.";
        }
      }
    },
    setHTML: function (html) {
      this.code = null;
      this.error = html;
    },
  },
};
</script>

<template>
  <div class="alert alert-danger" role="alert" v-if="error" v-cloak>
    <h4 class="modal-title" id="ErrorLabel">
      <template v-if="showTitle">Error {{ code }}</template>
      <button type="button" class="close" aria-label="Close" @click.prevent="clear">
        <span aria-hidden="true">&times;</span>
      </button>
    </h4>

    <div class="pr-3">
      <p v-html="error"></p>
    </div>
  </div>
</template>
