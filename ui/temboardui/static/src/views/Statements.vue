<script setup>
import _ from "lodash";
import moment from "moment";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router/composables";

import DateRangePicker from "../components/DateRangePicker/DateRangePicker.vue";
import { formatDuration } from "../utils/duration";

const router = useRouter();
const route = useRoute();

let dataRequest;
let chartRequest;

const statements = ref([]);
const metas = ref(null);
const isLoading = ref(true);
const dbid = ref(route.query.dbid);
const queryid = ref(route.query.queryid);
const userid = ref(route.query.userid);
const datname = ref(null);
const sortBy = ref("total_exec_time");
const filter = ref("");
const from = ref(null);
const to = ref(null);
const totalRows = ref(1);
const currentPage = ref(1);
const perPage = ref(20);
const dateRangePickerEl = ref(null);

const fields = computed(getFields);
const fromTo = computed(() => "" + from.value + to.value);
const queryidUserid = computed(() => {
  return queryid.value, userid.value;
});

watch(fromTo, fetchData);
watch(dbid, () => {
  const newQueryParams = _.assign({}, route.query);
  if (!dbid.value) {
    delete newQueryParams.dbid;
    delete newQueryParams.queryid;
    delete newQueryParams.userid;
  } else {
    newQueryParams.dbid = dbid.value;
  }
  router.push({ query: newQueryParams });
  fetchData();
});

watch(queryidUserid, () => {
  const newQueryParams = _.assign({}, route.query.value);
  if (!queryid.value) {
    delete newQueryParams.queryid;
    delete newQueryParams.userid;
  } else {
    newQueryParams.dbid = dbid.value;
    newQueryParams.queryid = queryid.value;
    newQueryParams.userid = userid.value;
  }
  router.push({ query: newQueryParams });
  fetchData();
});

watch(route, (oldVal, newVal) => {
  dbid.value = newVal.query.dbid;
  queryid.value = newVal.query.queryid;
  userid.value = newVal.query.userid;
});

function fetchData() {
  statements.value = [];
  const startDate = from.value;
  const endDate = to.value;

  let url = dbid.value ? "/" + dbid.value : "";
  url += queryid.value ? "/" + queryid.value : "";
  url += userid.value ? "/" + userid.value : "";

  isLoading.value = true;
  dataRequest && dataRequest.abort();
  dataRequest = $.get(
    apiUrl + url,
    {
      start: timestampToIsoDate(startDate),
      end: timestampToIsoDate(endDate),
      noerror: 1,
    },
    function (data) {
      isLoading.value = false;
      datname.value = data.datname;
      statements.value = data.data;
      // automatically show detail if a single query is displayed
      if (queryid.value) {
        statements.value[0]._showDetails = true;
      }
      totalRows.value = statements.value.length;

      metas.value = data.metas;
    },
  );

  chartRequest && chartRequest.abort();
  chartRequest = $.get(
    chartApiUrl + url,
    {
      start: timestampToIsoDate(startDate),
      end: timestampToIsoDate(endDate),
      noerror: 1,
    },
    createOrUpdateCharts,
  );
}

function getFields() {
  const fields = [
    {
      key: "query",
      label: "Query",
      class: "query",
      sortable: true,
      sortDirection: "asc",
    },
    {
      key: "datname",
      label: "DB",
      class: "database",
      sortable: true,
      sortDirection: "asc",
    },
    {
      key: "rolname",
      label: "User",
      sortable: true,
      sortDirection: "asc",
    },
    {
      key: "calls",
      label: "Calls",
      class: "text-right",
      sortable: true,
    },
    {
      key: "total_exec_time",
      label: "Total",
      formatter: formatDuration,
      class: "text-right border-left",
      sortable: true,
    },
    {
      key: "mean_time",
      label: "AVG",
      formatter: formatDuration,
      class: "text-right",
      sortable: true,
    },
    {
      key: "shared_blks_read",
      label: "Read",
      class: "text-right border-left",
      formatter: formatSize,
      sortable: true,
    },
    {
      key: "shared_blks_hit",
      label: "Hit",
      class: "text-right",
      formatter: formatSize,
      sortable: true,
    },
    {
      key: "shared_blks_dirtied",
      label: "Dirt.",
      class: "text-right",
      formatter: formatSize,
      sortable: true,
    },
    {
      key: "shared_blks_written",
      label: "Writ.",
      class: "text-right",
      formatter: formatSize,
      sortable: true,
    },
    {
      key: "temp_blks_read",
      label: "Read",
      class: "text-right border-left",
      formatter: formatSize,
      sortable: true,
    },
    {
      key: "temp_blks_written",
      label: "Writ.",
      class: "text-right",
      formatter: formatSize,
      sortable: true,
    },
  ];
  let ignored = ["rolname", "query"];

  if (dbid.value) {
    ignored = ["datname"];
  }

  return _.filter(fields, function (field) {
    return ignored.indexOf(field.key) === -1;
  });
}

function formatSize(bytes) {
  bytes *= 8192;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  if (bytes == 0) {
    return '<span class="text-muted">0</span>';
  }
  const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
  return Math.round(bytes / Math.pow(1024, i), 2) + " " + sizes[i];
}

function highlight(src) {
  return hljs.highlight("sql", src).value;
}

function onFiltered(filteredItems) {
  totalRows.value = filteredItems.length;
  currentPage.value = 1;
}

function timestampToIsoDate(epochMs) {
  return new Date(epochMs).toISOString();
}

function createOrUpdateCharts(data) {
  const startDate = from.value;
  const endDate = to.value;
  const defaultOptions = {
    axisLabelFontSize: 10,
    yLabelWidth: 14,
    includeZero: true,
    legend: "always",
    labelsKMB: true,
    gridLineColor: "rgba(128, 128, 128, 0.3)",
    dateWindow: [new Date(startDate).getTime(), new Date(endDate).getTime()],
    xValueParser: function (x) {
      const m = moment(x);
      return m.toDate().getTime();
    },
    zoomCallback: onChartZoom,
    // change interaction model in order to be able to capture the end of
    // panning
    // Dygraphs doesn't provide any panCallback unfortunately
    interactionModel: {
      mousedown: function (event, g, context) {
        context.initializeMouseDown(event, g, context);
        if (event.shiftKey) {
          Dygraph.startPan(event, g, context);
        } else {
          Dygraph.startZoom(event, g, context);
        }
      },
      mousemove: function (event, g, context) {
        if (context.isPanning) {
          Dygraph.movePan(event, g, context);
        } else if (context.isZooming) {
          Dygraph.moveZoom(event, g, context);
        }
      },
      mouseup: function (event, g, context) {
        if (context.isPanning) {
          Dygraph.endPan(event, g, context);
          const dates = g.dateWindow_;
          // synchronize charts on pan end
          onChartZoom(dates[0], dates[1]);
        } else if (context.isZooming) {
          Dygraph.endZoom(event, g, context);
          // don't do the same since zoom is animated
          // zoomCallback will do the job
        }
      },
    },
  };

  const chart1Data = _.map(data.data, function (datum) {
    return [moment.unix(datum.ts).toDate(), datum.calls];
  });
  new Dygraph(
    document.getElementById("chart1"),
    chart1Data,
    Object.assign({}, defaultOptions, {
      labels: ["time", "Queries per sec"],
      labelsDiv: "legend-chart1",
    }),
  );

  const chart2Data = _.map(data.data, function (datum) {
    return [moment.unix(datum.ts).toDate(), datum.load, datum.avg_runtime];
  });
  new Dygraph(
    document.getElementById("chart2"),
    chart2Data,
    Object.assign({}, defaultOptions, {
      labels: ["time", "Time per sec", "Avg runtime"],
      labelsDiv: "legend-chart2",
      axes: {
        y: {
          valueFormatter: formatDuration,
          axisLabelFormatter: formatDuration,
        },
      },
    }),
  );

  const chart3Data = _.map(data.data, function (datum) {
    return [moment.unix(datum.ts).toDate(), datum.total_blks_hit, datum.total_blks_read];
  });
  new Dygraph(
    document.getElementById("chart3"),
    chart3Data,
    Object.assign({}, defaultOptions, {
      labels: ["time", "Hit /s", "Read /s"],
      labelsDiv: "legend-chart3",
      axes: {
        y: {
          valueFormatter: formatSize,
          axisLabelFormatter: formatSize,
        },
      },
    }),
  );
}

function onChartZoom(min, max) {
  dateRangePickerEl.value.setFromTo(moment(min), moment(max));
}

function onFromToUpdate(from_, to_) {
  from.value = from_;
  to.value = to_;
}
</script>

<template>
  <div>
    <div class="row mb-1">
      <div class="col-12 d-flex justify-content-between" v-cloak>
        <nav aria-label="breadcrumb" class="d-inline-block">
          <ol class="breadcrumb">
            <li class="breadcrumb-item">
              <a
                href
                v-on:click.prevent="
                  dbid = null;
                  queryid = null;
                  userid = null;
                "
                v-if="dbid"
              >
                All Databases
              </a>
              <span v-else>All Databases</span>
            </li>
            <li class="breadcrumb-item" v-if="dbid">
              <em class="text-muted small">Database:</em>
              <a
                href
                v-on:click.prevent="
                  queryid = null;
                  userid = null;
                "
                v-if="queryid && userid"
              >
                {{ datname }}
              </a>
              <strong v-else>{{ datname }}</strong>
            </li>
            <li class="breadcrumb-item" v-if="queryid && userid">
              <em class="text-muted small">Query:</em>
              <strong>{{ queryid }}</strong>
            </li>
          </ol>
        </nav>
        <DateRangePicker @fromto-updated="onFromToUpdate" ref="dateRangePickerEl"></DateRangePicker>
      </div>
    </div>
    <div class="row mb-1">
      <div class="col d-flex" v-cloak v-if="metas && metas.error">
        <p class="alert alert-danger">
          {{ metas.error }}
        </p>
      </div>
    </div>
    <div class="row mb-1">
      <div class="col-sm-4">
        <div class="text-center">
          <strong>Calls</strong>
        </div>
        <div id="legend-chart1" class="legend-chart"></div>
        <div id="chart1" style="width: 100%; height: 150px"></div>
      </div>
      <div class="col-sm-4">
        <div class="text-center">
          <strong>Time</strong>
        </div>
        <div id="legend-chart2" class="legend-chart"></div>
        <div id="chart2" style="width: 100%; height: 150px"></div>
      </div>
      <div class="col-sm-4">
        <div class="text-center">
          <strong>Blocks</strong>
        </div>
        <div id="legend-chart3" class="legend-chart"></div>
        <div id="chart3" style="width: 100%; height: 150px"></div>
      </div>
    </div>
    <div class="row mb-1" v-cloak>
      <div class="col-6 offset-6">
        <b-form-group label="Filter" label-cols-sm="3" label-align-sm="right" label-for="filterInput" class="mb-0">
          <b-input-group>
            <b-form-input v-model="filter" type="search" id="filterInput" placeholder="Type to Search"></b-form-input>
            <b-input-group-append>
              <b-button id="buttonClearFilter" :disabled="!filter" @click="filter = ''">Clear</b-button>
            </b-input-group-append>
          </b-input-group>
        </b-form-group>
      </div>
    </div>
    <b-table
      striped
      small
      :items="statements"
      :fields="fields"
      :sort-by="sortBy"
      :busy="isLoading"
      :current-page="currentPage"
      :per-page="perPage"
      sort-desc
      show-empty
      v-cloak
      :filter="filter"
      @filtered="onFiltered"
      class="table-query"
    >
      <template v-slot:table-busy>
        <div class="text-center text-danger my-2">
          <b-spinner class="align-middle"></b-spinner>
          <strong>Loading...</strong>
        </div>
      </template>
      <template v-slot:thead-top="data">
        <b-tr>
          <b-th :colspan="dbid ? 3 : 2"></b-th>
          <b-th class="text-center border-left" colspan="2">Time</b-th>
          <b-th class="text-center border-left" colspan="4">Shared Blocks</b-th>
          <b-th class="text-center border-left" colspan="2">Temp Blocks</b-th>
        </b-tr>
      </template>
      <template v-slot:cell(query)="row">
        <pre
          class="sql hljs"
          v-html="highlight(row.value)"
          v-on:click.prevent="
            queryid = row.item.queryid;
            userid = row.item.userid;
          "
        ></pre>
      </template>
      <template v-slot:cell(datname)="row">
        <a href v-on:click.prevent="dbid = row.item.dbid">
          {{ row.item.datname }}
        </a>
      </template>
      <template v-slot:row-details="row">
        <b-card class="detail">
          <b-row class="mb-2">
            <b-col>
              <pre class="sql hljs" v-html="highlight(row.item.query)"></pre>
            </b-col>
          </b-row>
        </b-card>
      </template>
      <template v-slot:cell()="data">
        <span v-html="data.value"></span>
      </template>
      <template v-slot:empty="scope">
        <div class="text-center">
          There are no records to show.
          <br />
          <span class="text-muted" v-if="!metas || metas.coalesce_seq < 2"
            >No snapshot has been done yet, please wait.</span
          >
          <span class="text-muted" v-else-if="metas.error">There are errors</span>
        </div>
      </template>
    </b-table>
    <div class="row" v-if="!queryid && !userid">
      <div class="col-6">
        <b-pagination
          v-model="currentPage"
          :total-rows="totalRows"
          :per-page="perPage"
          align="fill"
          size="sm"
          class="my-0"
        ></b-pagination>
      </div>
    </div>
  </div>
</template>
