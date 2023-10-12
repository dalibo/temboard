<script type="text/javascript">
/* A simple boostrap Dialog */
export default {
  props: ["id", "title"],
  mounted() {
    $(this.$el).on("hidden.bs.modal", () => {
      this.$emit("closed");
    });
  },
};
</script>

<template>
  <div v-bind:id="id" class="modal fade" role="dialog" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h4 class="modal-title">{{ title }}</h4>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <slot></slot>
      </div>
    </div>
  </div>
</template>
