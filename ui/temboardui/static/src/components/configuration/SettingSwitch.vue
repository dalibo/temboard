<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps(["id", "name", "setting"]);
const model = ref(props.setting == "on");

const label = computed(() => (model.value ? "on" : "off"));
watch(props, () => (model.value = props.setting == "on")); // on reset to default need to force refresh
</script>

<template>
  <div class="form-check form-switch">
    <label :for="id">{{ label }}</label>
    <input class="form-check-input" type="checkbox" role="switch" :id="id" :name="name" v-model="model" />
  </div>
</template>
