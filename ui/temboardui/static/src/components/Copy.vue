<script setup>
import { ref } from "vue";

const isHovered = ref(false);
const content = ref(null);
const copied = ref(false);
function handleHover(hovered) {
  isHovered.value = hovered;
}

function doCopy() {
  const range = document.createRange();
  const sel = window.getSelection();
  range.selectNodeContents(content.value);
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand("copy");
  copied.value = true;
}
</script>

<template>
  <div class="postition-relative" v-b-hover="handleHover" @click="doCopy" @mouseleave="copied = false">
    <div ref="content">
      <slot></slot>
    </div>
    <span
      class="copy position-absolute top-0 right-0 pr-1 pl-1 bg-secondary text-white rounded"
      :class="{ 'd-none': !isHovered }"
      >{{ copied ? "Copied to clipboard" : "Click to copy" }}</span
    >
  </div>
</template>
