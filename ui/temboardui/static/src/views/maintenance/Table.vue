<script setup>
import { UseTimeAgo } from "@vueuse/components";
import hljs from "highlight.js/lib/core";
import sql from "highlight.js/lib/languages/sql";
import "highlight.js/styles/default.css";
import _ from "lodash";
import { computed, provide, ref } from "vue";

import MaintenanceAnalyzeModal from "../../components/maintenance/AnalyzeModal.vue";
import MaintenanceReindexModal from "../../components/maintenance/ReindexModal.vue";
import MaintenanceScheduledAnalyzes from "../../components/maintenance/ScheduledAnalyzes.vue";
import MaintenanceScheduledReindexes from "../../components/maintenance/ScheduledReindexes.vue";
import MaintenanceScheduledVacuums from "../../components/maintenance/ScheduledVacuums.vue";
import SizeDistributionBar from "../../components/maintenance/SizeDistributionBar.vue";
import MaintenanceVacuumModal from "../../components/maintenance/VacuumModal.vue";

hljs.registerLanguage("sql", sql);

let getScheduledVacuumsTimeout;
let getScheduledAnalyzesTimeout;
let getScheduledReindexesTimeout;

const props = defineProps(["apiUrl", "instance", "database", "schema", "table", "maintenanceBaseUrl", "schemaApiUrl"]);
provide("instance", props.instance);
const dbName = ref(props.database);
provide("dbName", dbName);
const tableName = ref(props.table);
provide("tableName", tableName);
const indexSortCriteria = ref("total_bytes");
const indexSortCriterias = ref({
  name: ["Name", "asc"],
  total_bytes: ["Size", "desc"],
  bloat_ratio: ["Bloat", "desc"],
});
const loading = ref(true);

const table = ref({});
const scheduledVacuums = ref([]);
const scheduledAnalyzes = ref([]);
const scheduledReindexes = ref([]);
const reindexType = ref("");
const reindexElementName = ref(null);

function fetchData() {
  getData();
  getScheduledVacuums();
  getScheduledAnalyzes();
  getScheduledReindexes();
}

const indexesSorted = computed(() => {
  const sortOrder = indexSortCriterias.value[indexSortCriteria.value][1];
  return _.orderBy(table.value.indexes, indexSortCriteria.value, sortOrder);
});

const filteredScheduledReindexes = computed(() => {
  return _.filter(scheduledReindexes.value, function (reindex) {
    // only reindexes with defined table
    // others are for indexes
    return reindex.table == tableName.value;
  });
});

function getData() {
  $.ajax({
    url: props.apiUrl,
    contentType: "application/json",
    success: function (data) {
      table.value = data;
      data.indexes.forEach(function (index) {
        index.bloat_ratio = 0;
        if (index.total_bytes) {
          index.bloat_ratio = parseFloat((100 * (index.bloat_bytes / index.total_bytes)).toFixed(1));
        }
      });
      window.setTimeout(() => {
        $("pre code.sql").each(function (_, block) {
          hljs.highlightBlock(block);
        });
        $('[data-toggle="popover"]').popover();
      }, 1);
    },
    error: showError,
    complete: function () {
      loading.value = false;
    },
  });
}

function getScheduledVacuums() {
  window.clearTimeout(getScheduledVacuumsTimeout);
  const count = scheduledVacuums.value.length;
  $.ajax({
    url: props.apiUrl + "/vacuum/scheduled",
    contentType: "application/json",
    success: function (data) {
      scheduledVacuums.value = data;
      // refresh list
      getScheduledVacuumsTimeout = window.setTimeout(function () {
        getScheduledVacuums();
      }, 5000);

      // There are less vacuums than before
      // It may mean that a vacuum is finished
      if (data.length < count) {
        getData();
      }
    },
    error: showError,
  });
}

function doVacuum() {
  const fields = $("#vacuumForm").serializeArray();
  const mode = fields
    .filter(function (field) {
      return field.name == "mode";
    })
    .map(function (field) {
      return field.value;
    })
    .join(",");
  const data = {};
  if (mode) {
    data["mode"] = mode;
  }
  const datetime = fields
    .filter(function (field) {
      return field.name == "datetime";
    })
    .map(function (field) {
      return field.value;
    })
    .join("");
  if (datetime) {
    data["datetime"] = datetime;
  }
  $.ajax({
    method: "POST",
    url: props.apiUrl + "/vacuum",
    data: JSON.stringify(data),
    contentType: "application/json",
    success: getScheduledVacuums,
    error: showError,
  });
}

function cancelVacuum(id) {
  $.ajax({
    method: "DELETE",
    url: props.maintenanceBaseUrl + "/vacuum/" + id,
    contentType: "application/json",
    success: getScheduledVacuums,
    error: showError,
  });
}

function getScheduledAnalyzes() {
  window.clearTimeout(getScheduledAnalyzesTimeout);
  const count = scheduledAnalyzes.value.length;
  $.ajax({
    url: props.apiUrl + "/analyze/scheduled",
    contentType: "application/json",
    success: function (data) {
      scheduledAnalyzes.value = data;
      // refresh list
      getScheduledAnalyzesTimeout = window.setTimeout(function () {
        getScheduledAnalyzes();
      }, 5000);

      // There are less analyzes than before
      // It may mean that a analyze is finished
      if (data.length < count) {
        getData();
      }
    },
    error: showError,
  });
}

function doAnalyze() {
  const fields = $("#analyzeForm").serializeArray();
  const mode = fields
    .filter(function (field) {
      return field.name == "mode";
    })
    .map(function (field) {
      return field.value;
    })
    .join(",");
  const data = {};
  if (mode) {
    data["mode"] = mode;
  }
  const datetime = fields
    .filter(function (field) {
      return field.name == "datetime";
    })
    .map(function (field) {
      return field.value;
    })
    .join("");
  if (datetime) {
    data["datetime"] = datetime;
  }
  $.ajax({
    method: "POST",
    url: props.apiUrl + "/analyze",
    data: JSON.stringify(data),
    contentType: "application/json",
    success: getScheduledAnalyzes,
    error: showError,
  });
}

function cancelAnalyze(id) {
  $.ajax({
    method: "DELETE",
    url: props.maintenanceBaseUrl + "/analyze/" + id,
    contentType: "application/json",
    success: getScheduledAnalyzes,
    error: showError,
  });
}

function getScheduledReindexes() {
  window.clearTimeout(getScheduledReindexesTimeout);
  const count = scheduledReindexes.value.length;
  $.ajax({
    url: props.schemaApiUrl + "/reindex/scheduled",
    contentType: "application/json",
    success: function (data) {
      scheduledReindexes.value = data;
      // refresh list
      getScheduledReindexesTimeout = window.setTimeout(function () {
        getScheduledReindexes();
      }, 5000);

      // There are less reindexes than before
      // It may mean that a reindex is finished
      if (data.length < count) {
        getData();
      }
    },
    error: showError,
  });
}

function doReindex() {
  const fields = $("#reindexForm").serializeArray();
  const data = {};
  const datetime = fields
    .filter(function (field) {
      return field.name == "datetime";
    })
    .map(function (field) {
      return field.value;
    })
    .join("");
  if (datetime) {
    data["datetime"] = datetime;
  }
  // get the element type (either table or index)
  const elementType = fields
    .filter(function (field) {
      return field.name == "elementType";
    })
    .map(function (field) {
      return field.value;
    })
    .join("");
  // get the element name
  const element = fields
    .filter(function (field) {
      return field.name == elementType;
    })
    .map(function (field) {
      return field.value;
    })
    .join("");
  $.ajax({
    method: "POST",
    url: [props.schemaApiUrl, elementType, element, "reindex"].join("/"),
    data: JSON.stringify(data),
    contentType: "application/json",
    success: getScheduledReindexes,
    error: showError,
  });
}

function cancelReindex(id) {
  $.ajax({
    method: "DELETE",
    url: props.maintenanceBaseUrl + "/reindex/" + id,
    contentType: "application/json",
    success: getScheduledReindexes,
    error: showError,
  });
}

function getLatestX(x) {
  return function () {
    let auto = false;
    let date = null;
    const last_x = table.value["last_" + x];
    const last_autox = table.value["last_auto" + x];
    if (!last_x && last_autox) {
      auto = true;
      date = last_autox;
    } else if (last_x && !last_autox) {
      date = last_x;
    } else {
      auto = last_autox > last_x;
      date = auto ? last_autox : last_x;
    }
    return {
      auto: auto,
      date: date,
    };
  };
}

const getLatestVacuum = computed(getLatestX("vacuum"));
const getLatestAnalyze = computed(getLatestX("analyze"));

fetchData();
</script>

<template>
  <div>
    <h3>
      Table: <strong>{{ tableName }}</strong>
    </h3>
    <div class="text-center" v-if="loading">
      <img src="/images/ring-alt.svg" class="fa-fw fa-2x" />
    </div>
    <div v-cloak v-if="!loading">
      <div class="row mb-2">
        <div class="col">
          <size-distribution-bar
            height="10"
            :total="table.total_bytes"
            :cat1="table.table_size"
            :cat1raw="table.table_bytes"
            cat1label="Heap"
            :cat1bis="table.bloat_size"
            :cat1bisraw="table.bloat_bytes || 0"
            cat1bislabel="Heap Bloat"
            :cat2="table.index_size"
            :cat2raw="table.index_bytes"
            cat2label="Indexes"
            :cat2bis="table.index_bloat_size"
            :cat2bisraw="table.index_bloat_bytes"
            cat2bislabel="Indexes Bloat"
            :cat3="table.toast_size"
            :cat3raw="table.toast_bytes"
            cat3label="Toast"
          >
          </size-distribution-bar>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <dl>
            <dt>Total</dt>
            <dd>
              {{ table.total_size }}
              <br />
              <span class="text-muted">~ {{ table.row_estimate }} rows</span>
              <small class="text-muted">(~ {{ table.n_dead_tup }} dead)</small>
            </dd>
          </dl>
        </div>
        <div class="col">
          <dl>
            <dt>
              Heap
              <span class="bg-cat1 legend fa-fw d-inline-block">&nbsp;</span>
            </dt>
            <dd>
              {{ table.table_size }}
              <br />
              <em class="text-muted">
                Bloat:
                {{ parseInt((table.bloat_bytes / table.table_bytes) * 100) }}%
                <span class="small"> ({{ table.bloat_size }}) </span>
              </em>
            </dd>
          </dl>
        </div>
        <div class="col">
          <dl>
            <dt>
              Indexes
              <span class="bg-cat2 legend fa-fw d-inline-block">&nbsp;</span>
            </dt>
            <dd>
              {{ table.index_size }}
              <br />
              <em class="text-muted">
                Bloat:
                {{ parseInt((table.index_bloat_bytes / table.index_bytes) * 100) }}%
                <span class="small"> ({{ table.index_bloat_size }}) </span>
              </em>
            </dd>
          </dl>
        </div>
        <div class="col">
          <dl>
            <dt>
              <span class="bg-secondary legend fa-fw d-inline-block">&nbsp;</span>
              Toast
            </dt>
            <dd>
              {{ table.toast_size }}
            </dd>
          </dl>
        </div>
        <div class="col">
          <dl>
            <dt>Fill Factor</dt>
            <dd>{{ table.fillfactor }}%</dd>
          </dl>
        </div>
      </div>
      <div class="row">
        <div class="col-4">
          Last ANALYZE:
          <em :title="getLatestAnalyze.date">
            <strong v-if="getLatestAnalyze.date">
              <UseTimeAgo v-slot="{ timeAgo }" :time="getLatestAnalyze.date">
                {{ timeAgo }}
              </UseTimeAgo>
            </strong>
            <span v-else>N/A</span>
            <span v-if="getLatestAnalyze.auto">(auto)</span>
          </em>
          <span class="text-muted small" v-if="table.n_mod_since_analyze">
            (~ {{ table.n_mod_since_analyze }} rows modified since then)
          </span>
          <br />
          <small> {{ table.analyze_count }} analyzes - {{ table.autoanalyze_count }} auto analyzes </small>
        </div>
        <div class="col-4">
          Last VACUUM:
          <em :title="getLatestVacuum.date">
            <strong v-if="getLatestVacuum.date">
              <UseTimeAgo v-slot="{ timeAgo }" :time="getLatestVacuum.date">
                {{ timeAgo }}
              </UseTimeAgo>
            </strong>
            <span v-else>N/A</span>
            <span v-if="getLatestVacuum.auto">(auto)</span>
          </em>
          <br />
          <small> {{ table.vacuum_count }} vacuums - {{ table.autovacuum_count }} auto vacuums </small>
        </div>
      </div>
      <div class="row">
        <div class="col-4">
          <div>
            <button
              id="buttonAnalyze"
              type="button"
              class="btn btn-outline-secondary"
              data-toggle="modal"
              data-target="#analyzeModal"
            >
              ANALYZE
            </button>
            <MaintenanceAnalyzeModal @apply="doAnalyze" />
            <MaintenanceScheduledAnalyzes :scheduledAnalyzes="scheduledAnalyzes" @cancel="cancelAnalyze" />
          </div>
        </div>
        <div class="col-4">
          <div>
            <button
              id="buttonVacuum"
              type="button"
              class="btn btn-outline-secondary"
              data-toggle="modal"
              data-target="#vacuumModal"
            >
              VACUUM
            </button>
            <MaintenanceVacuumModal @apply="doVacuum" />
            <MaintenanceScheduledVacuums :scheduledVacuums="scheduledVacuums" @cancel="cancelVacuum" />
          </div>
        </div>
        <div class="col-4">
          <div>
            <button
              id="buttonReindex"
              type="button"
              class="btn btn-outline-secondary"
              data-toggle="modal"
              data-target="#reindexModal"
              v-on:click="
                reindexType = 'table';
                reindexElementName = table.name;
              "
            >
              REINDEX
            </button>
            <MaintenanceReindexModal
              :reindexType="reindexType"
              :reindexElementName="reindexElementName"
              @apply="doReindex"
            />
            <MaintenanceScheduledReindexes :scheduledReindexes="filteredScheduledReindexes" @cancel="cancelReindex" />
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <p class="text-danger" v-if="table.n_mod_since_analyze / table.n_live_tup > 0.5">
            <i class="fa fa-exclamation-triangle"></i>The number of modified rows since last analyze is high, you should
            consider lauching an ANALYZE
            <br />
            <span class="pl-4 text-muted margin-left">
              Out of date analyzes can result in stats not being accurate, which eventually leads to slow queries.
            </span>
          </p>
          <p class="text-danger" v-if="table.n_dead_tup / table.n_live_tup > 0.1">
            <i class="fa fa-exclamation-triangle"></i>The number of dead tuples is high, you should consider running a
            VACUUM.
            <br />
            <span class="pl-4 text-muted margin-left"> Dead tuples waste space and slow down queries. </span>
          </p>
          <p class="text-danger" v-if="table.bloat_bytes / table.table_bytes > 0.5">
            <i class="fa fa-exclamation-triangle"></i>Overall table bloat is high. You should consider running a Full
            VACUUUM.
            <br />
            <span class="pl-4 text-muted margin-left"> Table bloat wastes space and slows down queries. </span>
          </p>
          <p class="text-danger" v-if="table.index_bloat_bytes / table.index_bytes > 0.5">
            <i class="fa fa-exclamation-triangle"></i>Overall index bloat is high. You should consider running a Full
            VACUUUM or REINDEX.
            <br />
            <span class="pl-4 text-muted margin-left"> Index bloat wastes space and slows down queries. </span>
          </p>
        </div>
      </div>
      <div class="d-flex">
        <h4>
          Indexes <span class="text-muted small">({{ table.indexes.length }})</span>
        </h4>
        <div class="ml-auto">
          <button
            class="btn btn-sm btn-outline-secondary dropdown-toggle"
            type="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            Sort by {{ indexSortCriterias[indexSortCriteria][0] }}
          </button>
          <div class="dropdown-menu">
            <h6 class="dropdown-header">Sort by:</h6>
            <a
              v-for="(criteria, key) in indexSortCriterias"
              class="dropdown-item"
              href="#"
              v-on:click="indexSortCriteria = key"
            >
              <i :class="['fa fa-fw', { 'fa-check': indexSortCriteria == key }]"></i>
              {{ criteria[0] }}
            </a>
          </div>
        </div>
      </div>
      <table class="table table-sm table-query table-striped table-bordered">
        <tbody>
          <tr v-for="index in indexesSorted">
            <td class="index-name align-middle">
              <strong>{{ index.name }}</strong>
              <small> ({{ index.type }}) </small>
              <span v-if="index.tablespace">
                <em class="text-muted small">in </em>
                {{ index.tablespace }}
              </span>
            </td>
            <td class="index-size text-right align-middle">
              <span :class="[indexSortCriteria == 'total_bytes' ? 'font-weight-bold' : '']">
                {{ index.total_size }}
              </span>
              <small
                style="min-width: 70px"
                :class="[
                  'index-bloat',
                  'd-inline-block',
                  indexSortCriteria == 'bloat_ratio' ? 'font-weight-bold' : 'text-muted',
                ]"
              >
                <template v-if="index.bloat_bytes"> Bloat: {{ index.bloat_ratio.toFixed(1) }}% </template>
              </small>
            </td>
            <td class="index-scans align-middle text-right">
              <span class="badge badge-secondary" v-if="index.scans"> {{ index.scans }} scans </span>
            </td>
            <td class="query" width="80%">
              <pre><code class="sql">{{ index.def }}</code></pre>
            </td>
            <td class="reindex align-middle" width="5%">
              <button
                class="buttonReindex btn btn-outline-secondary btn-sm py-0"
                data-toggle="modal"
                data-target="#reindexModal"
                v-on:click="
                  reindexType = 'index';
                  reindexElementName = index.name;
                "
              >
                Reindex
              </button>
              <ul class="list list-unstyled mb-0" v-if="scheduledReindexes.length > 0">
                <template v-for="scheduledReindex in scheduledReindexes">
                  <li v-if="scheduledReindex.index == index.name">
                    <template v-if="scheduledReindex.status == 'todo'">
                      <em v-if="scheduledReindex.status == 'todo'">
                        <span class="text-muted" :title="scheduledReindex.datetime.toString()"
                          ><i class="fa fa-clock-o"></i>&nbsp;
                          <UseTimeAgo v-slot="{ timeAgo }" :time="scheduledReindex.datetime">{{
                            timeAgo
                          }}</UseTimeAgo></span
                        >
                      </em>
                      <button
                        class="buttonCancel btn btn-link py-0"
                        v-on:click="cancelReindex(scheduledReindex.id)"
                        v-if="scheduledReindex.status == 'todo'"
                      >
                        Cancel
                      </button>
                    </template>
                    <template v-else-if="scheduledReindex.status == 'doing'">
                      <em class="text-muted">
                        <img id="loadingIndicator" src="/images/ring-alt.svg" class="fa-fw" />
                        in progress
                      </em>
                    </template>
                    <template v-else-if="scheduledReindex.status == 'canceled'">
                      <em class="text-muted">canceled</em>
                    </template>
                    <template v-else>
                      <em class="text-muted">{{ scheduledReindex.status }}</em>
                    </template>
                  </li>
                </template>
              </ul>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
