<script setup>
import { UseTimeAgo } from "@vueuse/components";
import hljs from "highlight.js/lib/core";
import sql from "highlight.js/lib/languages/sql";
import "highlight.js/styles/default.css";
import _ from "lodash";
import { computed, provide, ref } from "vue";

import MaintenanceReindexModal from "../../components/maintenance/ReindexModal.vue";
import SizeDistributionBar from "../../components/maintenance/SizeDistributionBar.vue";

hljs.registerLanguage("sql", sql);

let getScheduledReindexesTimeout;

const props = defineProps(["apiUrl", "instance", "database", "schema", "maintenanceBaseUrl", "schemaApiUrl"]);
provide("instance", props.instance);
const dbName = ref(props.database);
provide("dbName", dbName);
const schemaName = ref(props.schema);
const sortCriteria = ref("total_bytes");
const sortCriterias = ref({
  name: ["Name", "asc"],
  total_bytes: ["Database Size", "desc"],
  tables_bytes: ["Tables Size", "desc"],
  tables_bloat_ratio: ["Tables Bloat", "desc"],
  indexes_bytes: ["Indexes Size", "desc"],
  indexes_bloat_ratio: ["Indexes Bloat", "desc"],
  toast_bytes: ["Toast Size", "desc"],
});
const indexSortCriteria = ref("total_bytes");
const indexSortCriterias = ref({
  name: ["Name"],
  total_bytes: ["Size", "desc"],
  bloat_ratio: ["Bloat", "desc"],
});
const scheduledReindexes = ref([]);
const loading = ref(true);
const schema = ref({});
const reindexElementName = ref(null);

const tablesSorted = computed(() => {
  const sortOrder = sortCriterias.value[sortCriteria.value][1];
  return _.orderBy(schema.value.tables, sortCriteria.value, sortOrder);
});

const indexesSorted = computed(() => {
  const sortOrder = indexSortCriterias.value[indexSortCriteria.value][1];
  return _.orderBy(schema.value.indexes, indexSortCriteria.value, sortOrder);
});

function fetchData() {
  getSchemaData();
  getScheduledReindexes();
}

function getSchemaData() {
  $.ajax({
    url: props.apiUrl,
    contentType: "application/json",
    success: function (data) {
      schema.value = data;

      schema.value.tables.forEach(function (table) {
        table.bloat_ratio = 0;
        if (table.table_bytes) {
          table.bloat_ratio = parseFloat((100 * (table.bloat_bytes / table.table_bytes)).toFixed(1));
        }
        table.index_bloat_ratio = 0;
        if (table.index_bytes) {
          table.index_bloat_ratio = parseFloat((100 * (table.index_bloat_bytes / table.index_bytes)).toFixed(1));
        }
      });
      schema.value.indexes.forEach(function (index) {
        index.bloat_ratio = 0;
        if (index.total_bytes) {
          index.bloat_ratio = parseFloat((100 * (index.bloat_bytes / index.total_bytes)).toFixed(1));
        }
      });
      window.setTimeout(() => {
        $("pre code.sql").each((_, block) => {
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

function getScheduledReindexes() {
  window.clearTimeout(getScheduledReindexesTimeout);
  const count = scheduledReindexes.value.length;
  $.ajax({
    url: props.apiUrl + "/reindex/scheduled",
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
        getSchemaData();
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
fetchData();
</script>
<template>
  <div>
    <h3 class="row">
      <div class="col">
        Schema: <strong>{{ schemaName }}</strong>
      </div>
      <div class="col text-right" v-cloak v-if="!loading && schema.size">
        Size: <strong>{{ schema.size }}</strong>
      </div>
    </h3>
    <div class="text-center" v-if="loading">
      <img src="/images/ring-alt.svg" class="fa-fw fa-2x" />
    </div>
    <div v-cloak v-if="!loading">
      <div class="d-flex">
        <h4>
          Tables <span class="text-muted small">({{ schema.tables.length }})</span>
        </h4>
        <div class="ml-auto">
          <button
            class="btn btn-sm btn-outline-secondary dropdown-toggle"
            type="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            Sort by {{ sortCriterias[sortCriteria][0] }}
          </button>
          <div class="dropdown-menu">
            <h6 class="dropdown-header">Sort by:</h6>
            <a v-for="(criteria, key) in sortCriterias" class="dropdown-item" href="#" v-on:click="sortCriteria = key">
              <i :class="['fa fa-fw', { 'fa-check': sortCriteria == key }]"></i>
              {{ criteria[0] }}
            </a>
          </div>
        </div>
      </div>
      <em v-if="!schema.tables.length">No table</em>
      <table class="table table-sm">
        <thead>
          <tr>
            <th></th>
            <th></th>
            <th class="text-center border-left">
              <div class="d-inline-block">
                <div class="progress border rounded-0" style="height: 7px; width: 10px">
                  <div class="progress-bar bg-cat1" role="progressbar" style="width: 100%"></div>
                </div>
              </div>
              Heap
            </th>
            <th class="text-center border-left">
              <div class="d-inline-block">
                <div class="progress border rounded-0" style="height: 7px; width: 10px">
                  <div class="progress-bar bg-cat2" role="progressbar" style="width: 100%"></div>
                </div>
              </div>
              Indexes
            </th>
            <th class="text-center border-left">
              <div class="d-inline-block">
                <div class="progress border rounded-0" style="height: 7px; width: 10px">
                  <div class="progress-bar bg-cat3" role="progressbar" style="width: 100%"></div>
                </div>
              </div>
              Toast
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(table, index) in tablesSorted">
            <tr v-bind:class="{ 'bg-light2': index % 2 == 0 }">
              <td class="temboard-table">
                <a
                  :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${schemaName}/table/${table.name}`"
                >
                  <strong>{{ table.name }}</strong>
                </a>
                <span v-if="table.tablespace">
                  <em class="tablespace text-muted small">in </em>
                  {{ table.tablespace }}
                </span>
              </td>
              <td
                :class="[
                  'temboard-table-total-size',
                  'text-right',
                  sortCriteria == 'total_bytes' ? 'font-weight-bold' : '',
                ]"
              >
                {{ table.total_size }}
              </td>
              <td class="heap text-right border-left">
                <span
                  v-if="table.table_bytes"
                  :class="['table-size', sortCriteria == 'table_bytes' ? 'font-weight-bold' : '']"
                >
                  {{ table.table_size }}
                </span>
                <template v-else> - </template>
                <small
                  style="min-width: 70px"
                  :class="[
                    'table-bloat',
                    'd-inline-block',
                    sortCriteria == 'bloat_ratio' ? 'font-weight-bold' : 'text-muted',
                  ]"
                >
                  <template v-if="table.bloat_bytes"> Bloat: {{ table.bloat_ratio.toFixed(1) }}% </template>
                </small>
              </td>
              <template v-if="table.n_indexes">
                <td class="indexes text-right border-left">
                  <span class="badge badge-secondary">
                    {{ table.n_indexes }}
                  </span>
                  <span class="d-inline-block" style="min-width: 80px">
                    <span
                      v-if="table.index_bytes"
                      :class="['index-size', sortCriteria == 'index_bytes' ? 'font-weight-bold' : '']"
                    >
                      {{ table.index_size }}
                    </span>
                    <template v-else> - </template>
                  </span>
                  <small
                    style="min-width: 70px"
                    :class="[
                      'index-bloat',
                      'd-inline-block',
                      sortCriteria == 'index_bloat_ratio' ? 'font-weight-bold' : 'text-muted',
                    ]"
                  >
                    <template v-if="table.index_bloat_bytes">
                      Bloat: {{ table.index_bloat_ratio.toFixed(1) }}%
                    </template>
                  </small>
                </td>
              </template>
              <td class="indexes text-center text-muted border-left small" v-else>
                <em> No index </em>
              </td>
              <td class="temboard-toast text-right border-left">
                <span
                  v-if="table.toast_bytes"
                  :class="['toast-size', sortCriteria == 'toast_bytes' ? 'font-weight-bold' : '']"
                >
                  {{ table.toast_size }}
                </span>
                <template v-else> - </template>
              </td>
            </tr>
            <tr v-bind:class="{ 'bg-light2': index % 2 == 0 }">
              <td colspan="6" class="border-top-0">
                <size-distribution-bar
                  height="7"
                  :total="schema.total_bytes"
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
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <div class="d-flex">
        <h4>
          Indexes <span class="text-muted small">({{ schema.indexes.length }})</span>
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
      <em v-if="!schema.tables.length">No index</em>
      <MaintenanceReindexModal reindexType="index" :reindexElementName="reindexElementName" @apply="doReindex" />
      <table class="table table-sm table-query table-striped table-bordered">
        <tbody>
          <tr v-for="index in indexesSorted">
            <td class="index">
              <strong>{{ index.name }}</strong>
              <small> ({{ index.type }}) </small>
              <br />
              <em class="text-muted small">on </em>
              <a
                :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${schemaName}/table/${index.tablename}`"
              >
                {{ index.tablename }}
              </a>
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
                :class="['d-inline-block', indexSortCriteria == 'bloat_ratio' ? 'font-weight-bold' : 'text-muted']"
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
                v-on:click="reindexElementName = index.name"
              >
                Reindex
              </button>
              <ul class="list list-unstyled mb-0" v-if="scheduledReindexes.length > 0">
                <template v-for="scheduledReindex in scheduledReindexes">
                  <li v-if="scheduledReindex.index == index.name">
                    <template v-if="scheduledReindex.status == 'todo'">
                      <em v-if="scheduledReindex.status == 'todo'">
                        <span class="text-muted" :title="scheduledReindex.datetime.toString()">
                          <i class="fa fa-clock-o"></i>
                          <span :title="scheduledReindex.datetime.toString()">
                            <UseTimeAgo v-slot="{ timeAgo }" :time="scheduledReindex.datetime">
                              {{ timeAgo }}
                            </UseTimeAgo>
                          </span>
                        </span>
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
