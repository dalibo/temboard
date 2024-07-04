<script setup>
import { UseTimeAgo } from "@vueuse/components";
import { inject } from "vue";

defineProps(["scheduledReindexes"]);
const instance = inject("instance");
const dbName = inject("dbName");
const emit = defineEmits(["cancel"]);
</script>

<template>
  <div v-if="scheduledReindexes.length">
    <a
      data-bs-toggle="collapse"
      href="#collapseScheduledReindexes"
      aria-expanded="false"
      aria-controls="collapseScheduledReindexes"
    >
      <i class="fa fa-clock-o"></i>
      {{ scheduledReindexes.length }} scheduled reindexes
    </a>
    <ul class="list list-unstyled collapse border rounded p-1" id="collapseScheduledReindexes">
      <li v-for="scheduledReindex in scheduledReindexes" class="pb-1 text-body-secondary">
        <pre class="mb-0 text-truncate">
        <code class="bg-light small">REINDEX
        <span v-if="!scheduledReindex.table &&
        !scheduledReindex.index"> DATABASE {{ scheduledReindex.dbname }}</span>
        <span v-if="scheduledReindex.table"> TABLE
        <a
        :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${scheduledReindex.schema}`">{{scheduledReindex.schema
        }}</a>.<a :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${scheduledReindex.schema}/table/${scheduledReindex.table}`">{{ scheduledReindex.table }}</a></span><span v-if="scheduledReindex.index"> INDEX <a :href="`/server/${instance.agentAddress}/${ instance.agentPort}/maintenance/${dbName}/schema/${scheduledReindex.schema}`">{{  scheduledReindex.schema }}</a>.{{  scheduledReindex.index }}
        </span>
        </code>
        </pre>
        <template v-if="scheduledReindex.status == 'todo'">
          <em>
            scheduled
            <span :title="scheduledReindex.datetime.toString()">
              <UseTimeAgo v-slot="{ timeAgo }" :time="scheduledReindex.datetime">
                {{ timeAgo }}
              </UseTimeAgo>
            </span>
          </em>
          <button
            class="btn btn-sm btn-outline-secondary py-0"
            v-on:click="emit('cancel', scheduledReindex.id)"
            v-if="scheduledReindex.status == 'todo'"
          >
            Cancel
          </button>
        </template>
        <template v-else-if="scheduledReindex.status == 'doing'">
          <em>
            <img id="loadingIndicator" src="/images/ring-alt.svg" class="fa-fw" />
            in progress
          </em>
        </template>
        <template v-else-if="scheduledReindex.status == 'canceled'">
          <em>canceled</em>
        </template>
        <template v-else>
          <em>{{ scheduledReindex.status }}</em>
        </template>
      </li>
    </ul>
  </div>
</template>
