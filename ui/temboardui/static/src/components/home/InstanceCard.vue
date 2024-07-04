<script setup>
import Dygraph from "dygraphs";
import "dygraphs/dist/dygraph.css";
import $ from "jquery";
import _ from "lodash";
import { computed, onMounted, ref, watch } from "vue";

import Checks from "./Checks.vue";
import Sparkline from "./Sparkline.vue";

const load1_data = ref(null);
const load1_last = ref("N/A");
const tps_data = ref(null);
const tps_last = ref("N/A");

const props = defineProps(["end", "index", "refreshInterval", "start", "status_value", "instance"]);

const dashboard_url = computed(() => {
  return ["/server", props.instance.agent_address, props.instance.agent_port, "dashboard"].join("/");
});

const hasMonitoring = computed(() => {
  return props.instance.plugins.indexOf("monitoring") != -1;
});

onMounted(() => {
  if (props.index >= 18) {
    return;
  }

  fetchTPS();
  fetchLoad1();
});

watch(
  () => props.index,
  (newValue) => {
    if (newValue >= 18) {
      load1_data.value = null;
      load1_last.value = null;
      tps_data.value = null;
      tps_last.value = null;
    }
  },
);

function fetchLoad1() {
  fetchMetric("load1").done((data) => {
    if (data) {
      load1_data.value = data;
    }
  });
}

function fetchTPS() {
  fetchMetric("tps").done((data) => {
    if (data) {
      tps_data.value = data;
    }
  });
}

function fetchMetric(metric) {
  var url = ["/server", props.instance.agent_address, props.instance.agent_port, "monitoring/data", metric].join("/");
  var params = "?start=" + props.start.toISOString() + "&end=" + props.end.toISOString();
  return $.get(url + params);
}

function setLastLoad1(last_value) {
  // Use Dygraphs to parse CSV and report last point in VueJS context.
  load1_last.value = last_value || "N/A";
}

function setLastTPS(last_value) {
  // Use Dygraphs to parse CSV and report last point in VueJS context.
  tps_last.value = last_value || "N/A";
}

defineExpose({ fetchLoad1, fetchTPS });
</script>

<template>
  <div
    :class="[
      'card',
      {
        'border-danger bg-danger-light': status_value >= 1000000,
        'border-warning bg-warning-light': status_value >= 1000,
      },
    ]"
  >
    <div class="card-body p-2" style="min-height: 150px">
      <div class="row">
        <div class="col-md-12">
          <p class="mb-0 overflow-ellipsis">
            <strong>
              <i class="fa fa-database"></i>
              <a
                :href="dashboard_url"
                :title="
                  instance.pg_version_summary + ' listening on ' + [instance.hostname, instance.pg_port].join(':')
                "
                class="instance-link"
                data-bs-toggle="tooltip"
              >
                {{ instance.hostname }}:{{ instance.pg_port }}
              </a>
            </strong>
          </p>
          <p class="mb-0 small">
            <template v-for="group in instance.groups">
              <span class="badge border text-body-secondary me-1" :title="'Instance in group ' + group">
                {{ group }}
              </span>
            </template>
            <span class="pg_version" :class="{ 'text-body-secondary': !instance.pg_version_summary }">{{
              instance.pg_version_summary || "Unknown version"
            }}</span>
          </p>
          <Checks :instance="instance"></Checks>
        </div>
      </div>
      <!-- Limit graph to top 3 rows. -->
      <div class="row" v-if="hasMonitoring && index < 18">
        <div class="col-md-6 mt-2 small text-center text-nowrap">
          <span class="text-body-secondary" v-if="tps_last">TPS: </span>
          <span class="badge text-bg-secondary" v-if="tps_last">
            {{ tps_last }}
          </span>
          <Sparkline
            :data="tps_data"
            :start="start"
            :end="end"
            :colors="['#50BD68', '#F15854']"
            @chart-rendered="setLastTPS"
            ref="tps_chart"
            class="sparkline-container"
            data-bs-toggle="tooltip"
            data-bs-title="Transations / sec (last hour)"
            data-bs-container="body"
            data-bs-placement="bottom"
          >
          </Sparkline>
        </div>
        <div class="col-md-6 mt-2 small text-center text-nowrap">
          <span class="text-body-secondary" v-if="load1_last">Loadavg: </span>
          <span class="badge text-bg-secondary" v-if="load1_last">
            {{ load1_last }}
          </span>
          <div
            ref="chart"
            data-bs-toggle="tooltip"
            data-bs-title="Load average (last hour)"
            data-bs-placement="bottom"
          ></div>
          <Sparkline
            :data="load1_data"
            :start="start"
            :end="end"
            :colors="['#FAA43A']"
            @chart-rendered="setLastLoad1"
            ref="load1_chart"
            class="sparkline-container"
            data-bs-toggle="tooltip"
            data-bs-title="Load average (last hour)"
            data-bs-placement="bottom"
          >
          </Sparkline>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sparkline-container {
  height: 30px;
}
</style>
