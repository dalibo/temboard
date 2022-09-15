<script type="text/javascript">
  // A Bootstrap grid row showing a global page error.

  export default {
    data: function() { return {
      // my* data avoid conflicts with props.
      myCode: null,
      myError: null
    }},
    props: ['error', 'code'],
    watch: {
      code: function(val) {
        this.myCode = val
      },
      error: function(val) {
        this.myError = val
      },
    },
    methods: {
      clear: function() {
        this.myError = null
        this.myCode = null
      },
      fromXHR: function(xhr) {
        if (0 === xhr.status) {
          this.myError = "Failed to contact server."
        }
        else if (xhr.getResponseHeader('content-type').includes('application/json')) {
          this.myCode = xhr.status
          this.myError = JSON.parse(xhr.responseText).error
        }
        else if ('text/plain' == xhr.getResponseHeader('content-type')) {
          this.myCode = xhr.status
          this.myError = `<pre>${xhr.responseText}</pre>`
        }
        else {
          this.myCode = xhr.status
          this.myError = 'Unknown error. Please contact temBoard administrator.'
        }
      }
    }
  }
</script>

<template>
  <div class="row justify-content-center" v-if="myError" v-cloak>
    <div id="divError" class="col col-xl-6 col-10">
      <div class="alert alert-danger" role="alert">
        <h4 class="modal-title" id="ErrorLabel">
          Error {{myCode}}
          <button type="button" class="close" aria-label="Close" @click.prevent="clear"><span aria-hidden="true">&times;</span></button>
        </h4>
        <p>{{myError}}</p>
      </div>
    </div>
  </div>
</template>
