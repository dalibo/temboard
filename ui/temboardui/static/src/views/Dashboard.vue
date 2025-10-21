<script setup>
import { UseTimeAgo } from "@vueuse/components";
import { useFullscreen } from "@vueuse/core";
import { Popover } from "bootstrap";
import { filesize } from "filesize";
import $ from "jquery";
import { computed, onMounted, ref } from "vue";

import { stateBorderClass } from "../utils/state";

// FIXME import chart.js and moment
const props = defineProps(["config", "instance", "discover", "jdataHistory", "initialData"]);
const dashboard = ref(props.initialData);
const discover = ref(props.discover);
const memory = ref(props.initialData.memory.total);
const databases = props.initialData.databases;
// total_size is formated by agent. Use total_size_bytes when dropping agent v8.
const totalSize = ref(databases ? databases.total_size : null);
// Using databases.databases for v8 compat. Use databases.nb later.
const nbDb = ref(databases ? databases.databases : null);
const loadAverage = ref(props.initialData.loadaverage);
const status = ref(null);
const totalMemory = ref(0);
const totalHit = ref(" ");
const totalCpu = ref(" ");
const totalSessions = ref(0);
const tpsCommit = ref(0);
const tpsRollback = ref(0);
const alerts = ref([]);
const states = ref([]);
const moment = window.moment;

// Elements refs
const memoryChartEl = ref(null);
const cpuChartEl = ref(null);
const hitRatioChartEl = ref(null);
const sessionsChartEl = ref(null);
const tpsChartEl = ref(null);
const loadAverageChartEl = ref(null);
const divAlertsEl = ref(null);
const rootEl = ref(null);
const error = ref(null);

const { toggle } = useFullscreen(rootEl);

// Charts objects
let memoryChart;
let cpuChart;
let hitRatioChart;
let sessionsChart;
let tpsChart;
let loadAverageChart;

let timeRange;
let popoverList = [];

const cpuTooltip = computed(() => {
  const count = discover.value.system.cpu_count;
  const model = discover.value.system.cpu_model;
  return `${count} × ${model}`;
});

/*
 * Call the agent's dashboard API and update the view through
 * updateDashboard() callback.
 */
function refreshDashboard() {
  window.clearError();
  $.ajax({
    url: "/proxy/" + props.instance.agentAddress + "/" + props.instance.agentPort + "/dashboard",
    type: "GET",
    async: true,
    contentType: "application/json",
    success: function (data) {
      status.value = data.status;
      updateDashboard(data);
      updateTps([data]);
      updateLoadaverage([data]);
    },
    error: function (xhr) {
      if (xhr.status == 401 || xhr.status == 302) {
        // force a reload of the page, should lead to the server login page
        location.href = location.href;
      }
      window.showError(chr);
    },
  });
}

function updateDashboard(data) {
  memory.value = filesize(data.memory.total * 1000);
  const databases = data["databases"];
  totalSize.value = databases ? databases.total_size : null;
  nbDb.value = databases ? databases.databases : null;

  /** Update memory usage chart **/
  memoryChart.data.datasets[0].data[0] = data["memory"]["active"];
  memoryChart.data.datasets[0].data[1] = data["memory"]["cached"];
  memoryChart.data.datasets[0].data[2] = data["memory"]["free"];
  memoryChart.update();
  updateTotalMemory();

  /** Update CPU usage chart **/
  cpuChart.data.datasets[0].data[0] = data["cpu"]["iowait"];
  cpuChart.data.datasets[0].data[1] = data["cpu"]["steal"];
  cpuChart.data.datasets[0].data[2] = data["cpu"]["user"];
  cpuChart.data.datasets[0].data[3] = data["cpu"]["system"];
  cpuChart.data.datasets[0].data[4] = data["cpu"]["idle"];
  cpuChart.update();
  updateTotalCpu();

  /** Hitratio chart **/
  hitRatioChart.data.datasets[0].data[0] = data["hitratio"];
  hitRatioChart.data.datasets[0].data[1] = 100 - data["hitratio"];
  hitRatioChart.update();
  updateTotalHit();

  /** Sessions chart **/
  const active_backends = data.active_backends;
  const nb_active_backends = active_backends ? active_backends.nb : null;
  sessionsChart.data.datasets[0].data[0] = nb_active_backends;
  sessionsChart.data.datasets[0].data[1] = discover.value.postgres.max_connections - nb_active_backends;
  sessionsChart.update();
  updateTotalSessions();
}

function updateTotalCpu() {
  // create a copy of data
  const data = cpuChart.data.datasets[0].data.slice(0);
  // last element is "idle", don't take it into account
  data.pop();
  totalCpu.value =
    parseInt(
      data.reduce(function (a, b) {
        return a + b;
      }, 0),
    ) + " %";
}

function updateTotalMemory() {
  // create a copy of data
  const data = memoryChart.data.datasets[0].data.slice(0);
  // last element is "Free", don't take it into account
  data.pop();
  totalMemory.value =
    parseInt(
      data.reduce(function (a, b) {
        return a + b;
      }, 0),
    ) + " %";
}

function updateTotalHit() {
  const value = hitRatioChart.data.datasets[0].data[0];
  totalHit.value = value ? value + " %" : "N/A";
}

function updateTotalSessions() {
  const data = sessionsChart.data.datasets[0].data;
  let html = data[0];
  if (data[1]) {
    html += " / " + (data[0] + data[1]);
  }
  totalSessions.value = html;
}

function updateTimeRange(chart) {
  // update date range
  const timeConfig = chart.options.scales.xAxes[0].time;
  const now = moment();
  timeConfig.min = now.clone().subtract(timeRange, "s");
  timeConfig.max = now;

  // Remove old data
  const datasets = chart.data.datasets;
  for (let i = 0; i < datasets.length; i++) {
    const dataset = datasets[i];
    dataset.data = dataset.data.filter(function (datum) {
      return datum.x > moment(chart.options.scales.xAxes[0].time.min).unix() * 1000;
    });
  }
  chart.update();
}

function updateLoadaverage(data) {
  /** Add the very new loadaverage value to the chart dataset ... **/
  const chart = loadAverageChart;
  updateTimeRange(chart);

  for (let i = 0; i < data.length; i++) {
    chart.data.datasets[0].data.push({
      x: data[i].timestamp * 1000,
      y: data[i].loadaverage,
    });
  }
  loadAverage.value = data[data.length - 1]["loadaverage"];
  chart.update();
}

function computeDelta(a, b, duration) {
  return Math.ceil((a - b) / duration);
}

// Track last datum to compute TPS.
let lastDatum = {};

function updateTps(data) {
  const chart = tpsChart;
  updateTimeRange(chart);

  const datasets = chart.data.datasets;
  const commitData = datasets[0].data;
  const rollbackData = datasets[1].data;

  if (data.length > 1) {
    // Initial call. Bootstrap first datum.
    lastDatum = data[0];
    data.shift();
  }

  let duration;
  for (let i = 0; i < data.length; i++) {
    const datum = data[i];
    const databases = datum.databases;

    duration = datum.timestamp - lastDatum.timestamp;
    if (duration === 0) {
      continue;
    }
    const deltaCommit = computeDelta(databases.total_commit, lastDatum.databases.total_commit, duration);
    const deltaRollback = computeDelta(databases.total_rollback, lastDatum.databases.total_rollback, duration);

    commitData.push({ x: datum.timestamp * 1000, y: deltaCommit });
    rollbackData.push({ x: datum.timestamp * 1000, y: deltaRollback });
    lastDatum = datum;
  }

  tpsCommit.value = commitData[commitData.length - 1].y;
  tpsRollback.value = rollbackData[rollbackData.length - 1].y;
  chart.update();

  $("#postgres-stopped-msg").toggleClass("d-none", !!data[data.length - 1].databases);
}

/**
 * Update status and alerts
 */
function updateAlerts() {
  window.clearError();
  $.ajax({
    url: "/server/" + props.instance.agentAddress + "/" + props.instance.agentPort + "/alerting/alerts.json",
    success: function (data) {
      // remove any previous popover to avoid conflicts with
      // recycled div elements
      popoverList.forEach((p) => p.dispose());
      alerts.value = data;
      window.setTimeout(function () {
        const popoverTriggerList = divAlertsEl.value.querySelectorAll("[data-bs-toggle-popover]");
        popoverList = [...popoverTriggerList].map(
          (el) =>
            new Popover(el, {
              placement: "top",
              container: "body",
              boundary: "window",
              content: function (el) {
                return $(el).find(".popover-content")[0].outerHTML.replace("d-none", "");
              },
              html: true,
            }),
        );
      }, 1);
    },
    error: function (xhr) {
      window.showError(xhr);
    },
  });

  window.clearError();
  $.ajax({
    url: "/server/" + props.instance.agentAddress + "/" + props.instance.agentPort + "/alerting/checks.json",
    success: function (data) {
      states.value = data;
    },
    error: function (xhr) {
      window.showError(xhr);
    },
  });
}

onMounted(() => {
  if (discover.value === null) {
    window.showError("UI does not know this agent. Retry in 1 minute or check the logs.");
    return;
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    legend: false,
    rotation: Math.PI,
    circumference: Math.PI,
  };

  memoryChart = new Chart(memoryChartEl.value.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: ["Active", "Cached", "Free"],
      datasets: [
        {
          backgroundColor: ["#cc2936", "#29cc36", "#eeeeee"],
        },
      ],
    },
    options: options,
  });

  cpuChart = new Chart(cpuChartEl.value.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: ["IO Wait", "Steal", "User", "System", "IDLE"],
      datasets: [
        {
          backgroundColor: ["#cc2936", "#cbff00", "#29cc36", "#cbff00", "#eeeeee"],
        },
      ],
    },
    options: options,
  });

  hitRatioChart = new Chart(hitRatioChartEl.value.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: ["Hit", "Read"],
      datasets: [
        {
          backgroundColor: ["#29cc36", "#cc2936"],
        },
      ],
    },
    options: options,
  });

  sessionsChart = new Chart(sessionsChartEl.value.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: ["Active backends", "Free"],
      datasets: [
        {
          backgroundColor: ["#29cc36", "#eeeeee"],
        },
      ],
    },
    options: options,
  });
  updateTotalSessions();

  const now = moment();
  timeRange = props.config.history_length * props.config.scheduler_interval;

  const lineChartsOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    legend: {
      display: false,
    },
    scales: {
      yAxes: [
        {
          ticks: {
            beginAtZero: true,
          },
        },
      ],
      xAxes: [
        {
          type: "time",
          time: {
            min: now.clone().subtract(timeRange, "s"),
            max: now,
            displayFormats: {
              second: "h:mm a",
              minute: "h:mm a",
            },
          },
        },
      ],
    },
    elements: {
      point: {
        radius: 0,
        hoverRadius: 0,
      },
      line: {
        borderWidth: 1,
      },
    },
    tooltips: {
      enabled: false,
    },
  };

  tpsChart = new Chart(tpsChartEl.value.getContext("2d"), {
    type: "line",
    data: {
      datasets: [
        {
          label: "Commit",
          backgroundColor: "rgba(0,188,18,0.2)",
          borderColor: "rgba(0,188,18,1)",
        },
        {
          label: "Rollback",
          backgroundColor: "rgba(188,0,0,0.2)",
          borderColor: "rgba(188,0,0,1)",
        },
      ],
    },
    options: lineChartsOptions,
  });
  updateTps(props.jdataHistory);

  loadAverageChart = new Chart(loadAverageChartEl.value.getContext("2d"), {
    type: "line",
    data: {
      datasets: [
        {
          label: "Loadaverage",
          backgroundColor: "rgba(250, 164, 58, 0.2)",
          borderColor: "rgba(250, 164, 58, 1)", //'#FAA43A'
        },
      ],
    },
    options: lineChartsOptions,
  });
  updateLoadaverage(props.jdataHistory);

  const refreshInterval = props.config.scheduler_interval * 1000;
  window.setInterval(refreshDashboard, refreshInterval);
  refreshDashboard();

  if (props.instance.plugins.includes("monitoring")) {
    // monitoring plugin enabled
    const alertRefreshInterval = 60 * 1000;
    window.setInterval(updateAlerts, alertRefreshInterval);
    updateAlerts();
  }
});
</script>

<template>
  <div ref="rootEl">
    <div class="position-absolute" style="z-index: 2">
      <button id="fullscreen" class="btn btn-link" @click="toggle">
        <i class="fa-solid fa-up-right-and-down-left-from-center"></i>
      </button>
    </div>
    <div class="row d-fullscreen">
      <div class="col d-flex justify-content-center">
        <strong class="bg-secondary p-2 border-radius-2 rounded text-white">
          {{ props.instance.hostname }}:{{ props.instance.pgPort }}
        </strong>
      </div>
    </div>
    <!-- charts row -->
    <div class="row mb-3" v-if="props.discover">
      <div class="col-xl-4 col-12 mb-3 mb-xl-0">
        <!-- System -->
        <div class="row">
          <div class="col-xl-12 col mb-xl-2">
            <div class="small text-body-secondary text-center">System</div>
            <div class="small text-center">
              {{ props.discover.system.distribution }} /
              <span id="os_version">{{ props.discover.system.os_version }}</span>
            </div>
            <div class="row mt-2">
              <div class="col-6 small text-center">
                <div class="chart-title">
                  CPU &times; {{ discover.system.cpu_count }}
                  <i
                    id="cpu-info"
                    class="fa-solid fa-info-circle text-body-secondary"
                    data-bs-toggle="tooltip"
                    :title="cpuTooltip"
                  >
                  </i>
                </div>
                <div id="total-cpu" class="fw-bold" v-html="totalCpu"></div>
                <div class="card-body p-2 chart-small">
                  <canvas ref="cpuChartEl"></canvas>
                </div>
              </div>
              <div class="col-6 small text-center">
                <div class="chart-title">Memory</div>
                <div>
                  <span id="total-memory" class="fw-bold" v-html="totalMemory"></span>
                  of
                  <span id="memory" class="fw-bold">{{ memory }}</span>
                </div>
                <div class="card-body p-2 chart-small">
                  <canvas ref="memoryChartEl"></canvas>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Postgres -->
        <div class="row">
          <div class="col-xl-12 col mb-xl-2">
            <div class="small text-body-secondary text-center">
              {{ discover.postgres.version_summary }}
              <template v-if="status">
                <span
                  v-if="status.postgres.primary && status.postgres.is_standby"
                  class="badge badge-secondary"
                  :title="status.postgres.primary_conninfo"
                  >secondary</span
                >
                <span v-else class="badge badge-primary">primary</span>
              </template>
            </div>
            <div class="small text-center">
              <b>
                <span id="nb_db" v-if="nbDb">
                  {{ nbDb }}
                </span>
              </b>
              Databases -
              <b id="size" v-if="totalSize">
                {{ totalSize }}
              </b>
              <br />
              <span :title="moment(discover.postgres.start_time).format('LLLL')">
                Start Time:
                <strong id="pg_start_time">
                  <UseTimeAgo v-slot="{ timeAgo }" :time="moment(discover.postgres.start_time)">
                    {{ timeAgo }}
                  </UseTimeAgo>
                </strong>
              </span>
            </div>
            <div class="row mt-2 position-relative">
              <div class="col-6 small text-center">
                <div class="chart-title">Cache Hit Ratio</div>
                <div id="total-hit" class="fw-bold">{{ totalHit }}</div>
                <div class="card-body p-2 chart-small">
                  <canvas ref="hitRatioChartEl"></canvas>
                </div>
              </div>
              <div class="col-6 small text-center">
                <div class="chart-title">Sessions</div>
                <div id="total-sessions" class="fw-bold">{{ totalSessions }}</div>
                <div class="card-body p-2 chart-small">
                  <canvas ref="sessionsChartEl"></canvas>
                </div>
              </div>
              <div
                id="postgres-stopped-msg"
                style="
                  position: absolute;
                  width: 100%;
                  height: 100%;
                  top: 0;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  opacity: 0.9;
                "
                class="alert alert-warning border border-warning d-none"
              >
                <div class="text-center">
                  <i class="fa-solid fa-exclamation-triangle fa-2x"></i>
                  <br />
                  PostgreSQL instance
                  <br />
                  is unreachable
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-8 col-12">
        <div class="h-50 pb-3">
          <div class="card h-100">
            <div class="text-center small p-0">
              <span class="chart-title"> Loadaverage </span>
              <div class="position-absolute top-0 right-0 pe-1">
                <span id="loadaverage" class="badge text-bg-primary">{{ loadAverage }}</span>
              </div>
            </div>
            <div class="card-body p-2">
              <div id="canvas-loadaverage-holder" class="canvas-wrapper chart-h-min chart-h-min-xl-0">
                <canvas id="chart-loadaverage" ref="loadAverageChartEl" />
              </div>
            </div>
          </div>
        </div>
        <div class="h-50">
          <div class="card h-100">
            <div class="text-center small p-0">
              <span class="chart-title"> TPS </span>
              <div class="position-absolute top-0 right-0 pe-1">
                Commit: <span id="tps_commit" class="badge text-bg-success">{{ tpsCommit }}</span> Rollback:
                <span id="tps_rollback" class="badge text-bg-danger">{{ tpsRollback }}</span>
              </div>
            </div>
            <div class="card-body p-2">
              <div id="canvas-tps-holder" class="canvas-wrapper chart-h-min chart-h-min-xl-0">
                <canvas id="chart-tps" ref="tpsChartEl" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="row" v-if="props.discover && props.instance.plugins.includes('monitoring')">
      <div class="col-8 position-relative">
        <div class="text-center small">
          Current status
          <div class="position-absolute top-0 right-0 pe-2">
            <a href="alerting" class="small text-body-secondary">More&hellip;</a>
          </div>
        </div>
        <div class="row small mb-2">
          <template v-for="state in states">
            <div class="col-3 col-xxl-2 p-1 text-center" v-if="state.state != 'UNDEF'">
              <div
                class="p-1 rounded"
                v-bind:class="[stateBorderClass(state.state), { 'striped bg-light': !state.enabled }]"
              >
                <a v-bind:href="'alerting/' + state.name" v-bind:class="{ 'text-body-secondary': !state.enabled }">
                  <div
                    class="text-nowrap fw-bold"
                    style="overflow: hidden; text-overflow: ellipsis"
                    v-bind:title="state.description"
                  >
                    {{ state.description }}
                  </div>
                  <div class="text-center">
                    <span class="badge" v-bind:class="'text-bg-' + state.state.toLowerCase()">{{ state.state }}</span>
                  </div>
                </a>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div class="col-4">
        <div class="text-center small">Last alerts</div>
        <div class="small" style="max-height: 300px; overflow-y: auto">
          <div class="text-center" v-if="!alerts">
            <div class="progress">
              <div class="progress-bar progress-bar-striped" style="width: 100%">Please wait ...</div>
            </div>
          </div>
          <div class="text-body-secondary text-center" v-if="alerts.length == 0">No alerts</div>
          <div v-cloak class="mb-0" ref="divAlertsEl">
            <template v-for="alert in alerts">
              <div
                class="bg-light mb-1"
                :data-bs-toggle-popover="alert.state == 'WARNING' || alert.state == 'CRITICAL'"
                data-bs-trigger="hover"
              >
                <div class="p-1">
                  <div class="float-end text-body-secondary text-end">{{ moment(alert.datetime).fromNow() }}<br /></div>
                  <div>
                    <a v-bind:href="'alerting/' + alert.name">
                      <span class="small text" v-bind:class="'text-' + alert.state.toLowerCase()">
                        <i class="fa-solid fa-square"></i>
                      </span>
                      <span>
                        {{ alert.description }}
                      </span>
                      <span v-if="alert.key">
                        -
                        {{ alert.key }}
                      </span>
                    </a>
                  </div>
                  <div
                    class="popover-content text-body-secondary d-none"
                    v-if="alert.state == 'WARNING' || alert.state == 'CRITICAL'"
                  >
                    {{ moment(alert.datetime).format() }}<br />
                    <span v-bind:class="'badge text-bg-' + alert.state.toLowerCase()">{{ alert.state }}</span>
                    <br />
                    <span class="fw-bold">
                      {{ alert.value }}
                    </span>
                    <br />
                    Thresholds: warning {{ alert.warning }} / critical {{ alert.critical }}
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
