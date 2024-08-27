<script setup>
/* A simple boostrap Dialog */
import { Modal } from "bootstrap";
import $ from "jquery";
import { onMounted, ref } from "vue";

defineProps(["id", "title"]);
const emit = defineEmits(["opening", "closed"]);
const root = ref(null);
let modal = null;

function show() {
  modal.show();
}

function hide() {
  modal.hide();
}

defineExpose({ hide, show });

onMounted(() => {
  modal = new Modal(root.value);
  root.value.addEventListener("show.bs.modal", () => {
    emit("opening");
  });
  root.value.addEventListener("hidden.bs.modal", () => {
    emit("closed");
  });
});
</script>

<template>
  <div v-bind:id="id" ref="root" class="modal fade" role="dialog" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h4 class="modal-title">{{ title }}</h4>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>

        <slot></slot>
      </div>
    </div>
  </div>
</template>
