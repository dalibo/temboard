<script setup>
import _ from "lodash";
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import DateRangePicker from "../components/DateRangePicker/DateRangePicker.vue";
import MonitoringChart from "../components/MonitoringChart.vue";

const route = useRoute();
const router = useRouter();

const from = ref(null);
const to = ref(null);
const dateRangePickerEl = ref(null);

const colors = {
  blue: "#5DA5DA",
  blue2: "#226191",
  green: "#60BD68",
  red: "#F15854",
  gray: "#4D4D4D",
  light_gray: "#AAAAAA",
  orange: "#FAA43A",
};

const metrics = ref({
  Loadavg: {
    title: "Loadaverage",
    api: "loadavg",
    options: {
      colors: [colors.blue, colors.orange, colors.green],
      ylabel: "Loadaverage",
    },
    category: "system",
  },
  CPU: {
    title: "CPU Usage",
    api: "cpu",
    options: {
      colors: [colors.blue, colors.green, colors.red, colors.gray],
      ylabel: "%",
      stackedGraph: true,
    },
    category: "system",
  },
  CtxForks: {
    title: "Context switches and forks per second",
    api: "ctxforks",
    options: {
      colors: [colors.blue, colors.green],
    },
    category: "system",
  },
  Memory: {
    title: "Memory usage",
    api: "memory",
    options: {
      colors: [colors.light_gray, colors.green, colors.blue, colors.orange],
      ylabel: "Memory",
      labelsKMB: false,
      labelsKMG2: true,
      stackedGraph: true,
    },
    category: "system",
  },
  Swap: {
    title: "Swap usage",
    api: "swap",
    options: {
      colors: [colors.red],
      ylabel: "Swap",
      labelsKMB: false,
      labelsKMG2: true,
      stackedGraph: true,
    },
    category: "system",
  },
  FsSize: {
    title: "Filesystems size",
    api: "fs_size",
    options: {
      ylabel: "Size",
      labelsKMB: false,
      labelsKMG2: true,
    },
    category: "system",
  },
  FsUsage: {
    title: "Filesystems usage",
    api: "fs_usage",
    options: {
      ylabel: "%",
    },
    category: "system",
  },
  // PostgreSQL
  TPS: {
    title: "Transactions per second",
    api: "tps",
    options: {
      colors: [colors.green, colors.red],
      ylabel: "Transactions",
      stackedGraph: true,
    },
    category: "postgres",
  },
  InstanceSize: {
    title: "Instance size",
    api: "instance_size",
    options: {
      colors: [colors.blue],
      ylabel: "Size",
      stackedGraph: true,
      labelsKMB: false,
      labelsKMG2: true,
    },
    category: "postgres",
  },
  TblspcSize: {
    title: "Tablespaces size",
    api: "tblspc_size",
    options: {
      ylabel: "Size",
      stackedGraph: true,
      labelsKMB: false,
      labelsKMG2: true,
    },
    category: "postgres",
  },
  Sessions: {
    title: "Sessions",
    api: "sessions",
    options: {
      ylabel: "Sessions",
      stackedGraph: true,
    },
    category: "postgres",
  },
  Blocks: {
    title: "Blocks Hit vs Read per second",
    api: "blocks",
    options: {
      colors: [colors.red, colors.green],
      ylabel: "Blocks",
    },
    category: "postgres",
  },
  HRR: {
    title: "Blocks Hit vs Read ratio",
    api: "hitreadratio",
    options: {
      colors: [colors.blue],
      ylabel: "%",
    },
    category: "postgres",
  },
  Checkpoints: {
    title: "Checkpoints",
    api: "checkpoints",
    options: {
      ylabel: "Checkpoints",
      y2label: "Duration",
      series: {
        write_time: {
          axis: "y2",
        },
        sync_time: {
          axis: "y2",
        },
      },
    },
    category: "postgres",
  },
  WalFilesSize: {
    title: "WAL Files size",
    api: "wal_files_size",
    options: {
      colors: [colors.blue, colors.blue2],
      labelsKMB: false,
      labelsKMG2: true,
      ylabel: "Size",
    },
    category: "postgres",
  },
  WalFilesCount: {
    title: "WAL Files",
    api: "wal_files_count",
    options: {
      colors: [colors.blue, colors.blue2],
      ylabel: "WAL files",
    },
    category: "postgres",
  },
  WalFilesRate: {
    title: "WAL Files written rate",
    api: "wal_files_rate",
    options: {
      colors: [colors.blue],
      ylabel: "Byte per second",
      labelsKMB: false,
      labelsKMG2: true,
      stackedGraph: true,
    },
    category: "postgres",
  },
  WBuffers: {
    title: "Written buffers",
    api: "w_buffers",
    options: {
      ylabel: "Written buffers",
      stackedGraph: true,
    },
    category: "postgres",
  },
  Locks: {
    title: "Locks",
    api: "locks",
    options: {
      ylabel: "Locks",
    },
    category: "postgres",
  },
  WLocks: {
    title: "Waiting Locks",
    api: "waiting_locks",
    options: {
      ylabel: "Waiting Locks",
    },
    category: "postgres",
  },
});
const themes = [
  {
    title: "Performance",
    graphs: ["Loadavg", "CPU", "TPS", "Sessions"],
  },
  {
    title: "Locks",
    graphs: ["Locks", "WLocks", "Sessions"],
  },
  {
    title: "Size",
    graphs: ["FsSize", "InstanceSize", "TblspcSize", "WalFilesSize"],
  },
];

var graphs_ = route.query.graphs;
const initialGraphs = graphs_
  ? JSON.parse(graphs_)
  : JSON.parse(localStorage.getItem("graphs")) || [].concat(themes[0].graphs);
const graphs = ref(initialGraphs);

function isVisible(metric) {
  return graphs.value.includes(metric);
}

function setVisible(metric, event) {
  if (event.target.checked) {
    graphs.value.unshift(metric);
  } else {
    removeGraph(metric);
  }
}

function selectAll() {
  loadGraphs(Object.keys(metrics.value));
}

function unselectAll() {
  loadGraphs([]);
}

function updateLocalStorage() {
  localStorage.setItem("graphs", JSON.stringify(graphs.value));
}

function removeGraph(graph) {
  graphs.value.forEach(function (item, index) {
    if (item == graph) {
      graphs.value.splice(index, 1);
    }
  });
}

function loadGraphs(list) {
  // First clear the array (with mutation)
  while (graphs.value.length) {
    graphs.value.pop();
  }
  // Then add items (with mutation)
  list.forEach((item) => {
    graphs.value.push(item);
  });
}

function setFromTo(from, to) {
  dateRangePickerEl.value.setFromTo(from, to);
}

watch(graphs.value, () => {
  if (route.query.graphs !== graphs.value) {
    router.push({
      path: route.path,
      query: _.assign({}, route.query, {
        graphs: JSON.stringify(graphs.value),
      }),
    });
  }
  updateLocalStorage();
});

function onFromToUpdate(from_, to_) {
  from.value = from_;
  to.value = to_;
}
</script>

<template>
  <div id="charts-container">
    <div class="row form-group mb-2">
      <div class="col-12 d-flex justify-content-between">
        <a
          class="btn btn-outline-secondary collapse-toggle dropdown-toggle collapsed"
          data-toggle="collapse"
          href="#metrics"
          role="button"
          aria-expanded="false"
          aria-controls="metrics"
        >
          <i class="fa fa-area-chart"></i>
          Metrics
        </a>
        <DateRangePicker @fromto-updated="onFromToUpdate" ref="dateRangePickerEl"></DateRangePicker>
      </div>
    </div>

    <div class="collapse" id="metrics">
      <div class="card card-body bg-light mb-2">
        <div class="row mb-2">
          <div class="col-4">
            <span class="text-muted text-uppercase">System</span>
            <ul class="list-unstyled mb-0">
              <li v-for="(metric, key) in metrics">
                <div class="form-check" v-if="metric.category == 'system'">
                  <input
                    type="checkbox"
                    :id="'checkbox' + key"
                    class="form-check-input"
                    :checked="isVisible(key)"
                    v-on:change="setVisible(key, $event)"
                  />
                  <label class="form-check-label" :for="'checkbox' + key">
                    {{ metric.title }}
                  </label>
                </div>
              </li>
            </ul>
          </div>
          <div class="col-8">
            <span class="text-muted text-uppercase">Postgres</span>
            <div class="columns-2">
              <ul class="list-unstyled mb-0">
                <li v-for="(metric, key) in metrics">
                  <div class="form-check" v-if="metric.category == 'postgres'">
                    <input
                      type="checkbox"
                      :id="'checkbox' + key"
                      class="form-check-input"
                      :checked="isVisible(key)"
                      v-on:change="setVisible(key, $event)"
                    />
                    <label class="form-check-label" :for="'checkbox' + key">
                      {{ metric.title }}
                    </label>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div class="row">
          <div class="col-8">
            <ul class="list-unstyled list-inline mb-0">
              <li class="list-inline-item">
                <a href="#" v-on:click.prevent="selectAll">Select all</a>
              </li>
              <li class="list-inline-item">
                <a href="#" v-on:click.prevent="unselectAll">Unselect all</a>
              </li>
            </ul>
            <ul class="list-unstyled list-inline mb-0">
              Predefined themes:
              <li class="list-inline-item" v-for="theme in themes">
                <a href="#" v-on:click.prevent="loadGraphs(theme.graphs)">{{ theme.title }}</a>
              </li>
            </ul>
          </div>
          <div class="col-4 d-flex align-items-end justify-content-end">
            <button class="btn btn-outline-secondary" data-toggle="collapse" data-target="#metrics">Close</button>
          </div>
        </div>
      </div>
    </div>
    <div class="card w-100 mb-2" v-for="graph in graphs" :key="graph">
      <div class="card-header">
        {{ metrics[graph].title }}
        <a
          :href="'#/?graphs=[&quot;' + graph + '&quot;]&start=' + from + '&end=' + to"
          class="small ml-2"
          target="_blank"
          title="Link to this graph."
          ><i class="fa fa-external-link"></i
        ></a>
        <span class="copy"></span>
        <button type="button" class="close" aria-label="Close" v-on:click="removeGraph(graph)">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="card-body">
        <div :id="'nodata' + graph" class="nodata-chart text-center d-none alert alert-secondary p-1">
          No data available
        </div>
        <div :id="'legend' + graph" class="legend-chart">
          <div class="row">
            <div class="col-md-4 col-md-offset-4">
              <div class="progress">
                <div class="progress-bar progress-bar-striped" style="width: 100%">Loading, please wait ...</div>
              </div>
            </div>
          </div>
        </div>
        <MonitoringChart
          :graph="graph"
          :id="'chart' + graph"
          :metrics="metrics"
          :from="from"
          :to="to"
          @onZoom="setFromTo"
          v-if="from && to"
        ></MonitoringChart>
        <div :id="'visibility' + graph" class="visibility-chart"></div>
      </div>
    </div>
    <div class="text-center w-100">
      <a
        href="#"
        v-on:click="
          $('#metrics').collapse('show');
          window.scrollTo({ top: 0 });
        "
        class="btn btn-outline-secondary"
      >
        + More metrics
      </a>
    </div>
  </div>
</template>
