<script setup>
import _ from "lodash";
import { computed } from "vue";

const props = defineProps(["instance"]);
const available = computed(() => {
  return props.instance.available;
});
const checks = computed(() => {
  return _.countBy(props.instance.checks.map((state) => state.state));
});

function popoverContent(instance) {
  // don't show OK states
  const filtered = instance.checks.filter((check) => {
    return !["OK", "UNDEF"].includes(check.state);
  });
  const levels = ["CRITICAL", "WARNING"];
  // make sure we have higher levels checks first
  const ordered = _.sortBy(filtered, (check) => {
    return levels.indexOf(check.state);
  });
  const checksList = ordered.map((check) => {
    return `<span class="badge text-bg-${check.state.toLowerCase()}">${check.description}</span>`;
  });
  return checksList.join("<br>");
}
</script>

<template>
  <div
    class="d-inline-block"
    data-bs-toggle="popover"
    :data-bs-content="popoverContent(props.instance)"
    data-bs-trigger="hover"
    data-bs-placement="bottom"
    data-bs-container="body"
    data-bs-html="true"
  >
    <span class="badge text-bg-critical me-1" v-if="!available" title="Unable to connect to Postgres">UNAVAILABLE</span>
    <span class="badge text-bg-critical me-1" v-if="checks.CRITICAL"> CRITICAL: {{ checks.CRITICAL }}</span>
    <span class="badge text-bg-warning me-1" v-if="checks.WARNING"> WARNING: {{ checks.WARNING }}</span>
    <span class="badge text-bg-ok me-1" v-if="!checks.WARNING && !checks.CRITICAL && !checks.UNDEF && checks.OK"
      >OK</span
    >
  </div>
</template>
