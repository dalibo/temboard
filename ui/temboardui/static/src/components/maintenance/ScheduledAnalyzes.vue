<script setup>
import { UseTimeAgo } from "@vueuse/components";
import { inject } from "vue";

defineProps(["scheduledAnalyzes"]);
const instance = inject("instance");
const dbName = inject("dbName");
const emit = defineEmits(["cancel"]);
</script>
<template>
  <div v-if="scheduledAnalyzes.length">
    <a
      data-bs-toggle="collapse"
      href="#collapseScheduledAnalyzes"
      aria-expanded="false"
      aria-controls="collapseScheduledAnalyzes"
    >
      <i class="fa fa-clock-o"></i>
      {{ scheduledAnalyzes.length }} scheduled analyzes
    </a>
    <ul class="list list-unstyled collapse border rounded p-1" id="collapseScheduledAnalyzes">
      <li v-for="scheduledAnalyze in scheduledAnalyzes" class="pb-1 text-muted">
        <pre class="mb-0 text-truncate">
        <code class="bg-light small">ANALYZE<span v-if="scheduledAnalyze.table"> <a
                  :href="`/server/${instance.agentAddress}/${
                  instance.agentPort}/maintenance/${dbName}/schema/${scheduledAnalyze.schema}`">{{
                  scheduledAnalyze.schema }}</a>.<a
                  :href="`/server/${instance.agentAddress}/${ instance.agentPort}/maintenance/${dbName}/schema/${scheduledAnalyze.schema}/table/${scheduledAnalyze.table}`">{{ scheduledAnalyze.table }}</a></span>
        </code>
        </pre>
        <template v-if="scheduledAnalyze.status == 'todo'">
          <em>
            scheduled
            <span :title="scheduledAnalyze.datetime.toString()">
              <UseTimeAgo v-slot="{ timeAgo }" :time="scheduledAnalyze.datetime">
                {{ timeAgo }}
              </UseTimeAgo>
            </span>
          </em>
          <button
            class="btn btn-sm btn-outline-secondary py-0"
            v-on:click="emit('cancel', scheduledAnalyze.id)"
            v-if="scheduledAnalyze.status == 'todo'"
          >
            Cancel
          </button>
        </template>
        <template v-else-if="scheduledAnalyze.status == 'doing'">
          <em>
            <img id="loadingIndicator" src="/images/ring-alt.svg" class="fa-fw" />
            in progress
          </em>
        </template>
        <template v-else-if="scheduledAnalyze.status == 'canceled'">
          <em>canceled</em>
        </template>
        <template v-else>
          <em>{{ scheduledAnalyze.status }}</em>
        </template>
      </li>
    </ul>
  </div>
</template>
