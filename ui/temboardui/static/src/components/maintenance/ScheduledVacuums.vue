<script setup>
import { UseTimeAgo } from "@vueuse/components";
import { inject } from "vue";

defineProps(["scheduledVacuums"]);
const instance = inject("instance");
const dbName = inject("dbName");
const emit = defineEmits(["cancel"]);
</script>
<template>
  <div v-if="scheduledVacuums.length">
    <a
      data-bs-toggle="collapse"
      href="#collapseScheduledVacuums"
      aria-expanded="false"
      aria-controls="collapseScheduledVacuums"
    >
      <i class="fa fa-clock-o"></i>
      {{ scheduledVacuums.length }} scheduled vacuums
    </a>
    <ul class="list list-unstyled collapse border rounded p-1" id="collapseScheduledVacuums">
      <li v-for="scheduledVacuum in scheduledVacuums" class="pb-1 text-body-secondary">
        <pre class="mb-0 text-truncate">
        <code class="bg-light small">VACUUM
        <span v-if="scheduledVacuum.mode"> ({{ scheduledVacuum.mode.toUpperCase() }})</span>
        <span v-if="scheduledVacuum.table"> <a :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${scheduledVacuum.schema}`">{{ scheduledVacuum.schema }}</a>.<a :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${scheduledVacuum.schema}/table/${scheduledVacuum.table}`">{{ scheduledVacuum.table }}</a></span>
        </code>
        </pre>
        <template v-if="scheduledVacuum.status == 'todo'">
          <em>
            scheduled
            <span :title="scheduledVacuum.datetime.toString()">
              <UseTimeAgo v-slot="{ timeAgo }" :time="scheduledVacuum.datetime">
                {{ timeAgo }}
              </UseTimeAgo>
            </span>
          </em>
          <button
            class="btn btn-sm btn-outline-secondary py-0"
            v-on:click="emit('cancel', scheduledVacuum.id)"
            v-if="scheduledVacuum.status == 'todo'"
          >
            Cancel
          </button>
        </template>
        <template v-else-if="scheduledVacuum.status == 'doing'">
          <em>
            <img id="loadingIndicator" src="/images/ring-alt.svg" class="fa-fw" />
            in progress
          </em>
        </template>
        <template v-else-if="scheduledVacuum.status == 'canceled'">
          <em>canceled</em>
        </template>
        <template v-else>
          <em>{{ scheduledVacuum.status }}</em>
        </template>
      </li>
    </ul>
  </div>
</template>
