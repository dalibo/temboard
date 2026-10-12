<script setup>
import { BPopover } from "bootstrap-vue-next";
import _ from "lodash";
import { computed } from "vue";

import { stateIcon } from "../../utils/state";

const props = defineProps(["instance"]);
const available = computed(() => {
  return props.instance.available;
});
const checks = computed(() => {
  return _.countBy(props.instance.checks.map((state) => state.state));
});

function popoverContent(instance) {
  if (!available.value) {
    return `<span class="badge text-bg-danger">Unable to connect to Postgres</span>`;
  }
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
    return `<span class="badge text-bg-${check.state.toLowerCase()}"> <i class="fa fa-fw
    ${stateIcon(check.state)}"></i> ${check.description}</span>`;
  });
  return checksList.join("<br>");
}
</script>

<template>
  <BPopover>
    <template #target>
      <div class="d-inline-block">
        <span class="badge text-bg-critical me-1" v-if="!available">
          <i class="fa fa-fw fa-unlink"></i>
          UNAVAILABLE</span
        >
        <span class="badge text-bg-critical me-1" v-if="checks.CRITICAL">
          <i class="fa fa-fw" :class="stateIcon('CRITICAL')"></i>
          {{ checks.CRITICAL }}</span
        >
        <span class="badge text-bg-warning me-1" v-if="checks.WARNING">
          <i class="fa fa-fw" :class="stateIcon('WARNING')"></i>
          {{ checks.WARNING }}</span
        >
        <span class="badge text-bg-ok me-1" v-if="!checks.WARNING && !checks.CRITICAL && !checks.UNDEF && checks.OK"
          >OK</span
        >
      </div>
    </template>
    <div v-html="popoverContent(props.instance)"></div>
  </BPopover>
</template>
