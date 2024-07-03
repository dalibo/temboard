<script setup>
import $ from "jquery";
import _ from "lodash";
import { computed, provide, ref } from "vue";

import MaintenanceAnalyzeModal from "../../components/maintenance/AnalyzeModal.vue";
import MaintenanceReindexModal from "../../components/maintenance/ReindexModal.vue";
import MaintenanceScheduledAnalyzes from "../../components/maintenance/ScheduledAnalyzes.vue";
import MaintenanceScheduledReindexes from "../../components/maintenance/ScheduledReindexes.vue";
import MaintenanceScheduledVacuums from "../../components/maintenance/ScheduledVacuums.vue";
import SizeDistributionBar from "../../components/maintenance/SizeDistributionBar.vue";
import MaintenanceVacuumModal from "../../components/maintenance/VacuumModal.vue";

let getScheduledVacuumsTimeout;
let getScheduledAnalyzesTimeout;
let getScheduledReindexesTimeout;

const props = defineProps(["apiUrl", "instance", "database", "maintenanceBaseUrl"]);
provide("instance", props.instance);
const dbName = ref(props.database);
provide("dbName", dbName);
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
const loading = ref(true);

const database = ref({});
const scheduledVacuums = ref([]);
const scheduledAnalyzes = ref([]);
const scheduledReindexes = ref([]);
const reindexElementName = ref(null);

function fetchData() {
  getData();
  getScheduledVacuums();
  getScheduledAnalyzes();
  getScheduledReindexes();
}

const schemasSorted = computed(() => {
  const sortOrder = sortCriterias.value[sortCriteria.value][1];
  return _.orderBy(database.value.schemas, sortCriteria.value, sortOrder);
});

function getData() {
  $.ajax({
    url: props.apiUrl,
    contentType: "application/json",
    success: function (data) {
      database.value = data;

      database.value.schemas.forEach(function (schema) {
        schema.tables_bloat_ratio = 0;
        if (schema.tables_bytes) {
          schema.tables_bloat_ratio = parseFloat((100 * (schema.tables_bloat_bytes / schema.tables_bytes)).toFixed(1));
        }
        schema.indexes_bloat_ratio = 0;
        if (schema.indexes_bytes) {
          schema.indexes_bloat_ratio = parseFloat(
            (100 * (schema.indexes_bloat_bytes / schema.indexes_bytes)).toFixed(1),
          );
        }
      });
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
  $.ajax({
    method: "POST",
    url: [props.apiUrl, "reindex"].join("/"),
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
        Database: <strong>{{ dbName }}</strong>
      </div>
      <div class="col text-end" v-cloak v-if="!loading">
        Size: <strong>{{ database.total_size }}</strong>
      </div>
    </h3>
    <div class="text-center" v-if="loading">
      <img src="/images/ring-alt.svg" class="fa-fw fa-2x" />
    </div>
    <div v-cloak v-if="!loading">
      <div class="row">
        <div class="col-4">
          <div>
            <button
              id="buttonAnalyze"
              type="button"
              class="btn btn-outline-secondary"
              data-bs-toggle="modal"
              data-bs-target="#analyzeModal"
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
              data-bs-toggle="modal"
              data-bs-target="#vacuumModal"
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
              data-bs-toggle="modal"
              data-bs-target="#reindexModal"
              v-on:click="reindexElementName = database.name"
            >
              REINDEX
            </button>
            <MaintenanceReindexModal
              reindexType="database"
              :reindexElementName="reindexElementName"
              @apply="doReindex"
            />
            <MaintenanceScheduledReindexes :scheduledReindexes="scheduledReindexes" @cancel="cancelReindex" />
          </div>
        </div>
      </div>

      <div class="d-flex">
        <h4>
          Schemas <span class="text-muted small">({{ database.schemas.length }})</span>
        </h4>
        <div class="ms-auto">
          <button
            class="btn btn-sm btn-outline-secondary dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
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
    </div>
    <table class="table table-sm" v-cloak v-if="!loading">
      <thead>
        <tr>
          <th></th>
          <th></th>
          <th class="text-center border-start">
            Tables
            <div class="d-inline-block">
              <div class="progress border rounded-0" style="height: 7px; width: 10px">
                <div class="progress-bar bg-cat1" role="progressbar" style="width: 100%"></div>
              </div>
            </div>
          </th>
          <th class="text-center border-start">
            Indexes
            <div class="d-inline-block">
              <div class="progress border rounded-0" style="height: 7px; width: 10px">
                <div class="progress-bar bg-cat2" role="progressbar" style="width: 100%"></div>
              </div>
            </div>
          </th>
          <th class="text-center border-start">
            Toast
            <div class="d-inline-block">
              <div class="progress border rounded-0" style="height: 7px; width: 10px">
                <div class="progress-bar bg-secondary" role="progressbar" style="width: 100%"></div>
              </div>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(schema, loop_index) in schemasSorted">
          <tr v-bind:class="{ 'bg-light2': loop_index % 2 == 0 }">
            <td class="schema fw-bold">
              <a
                :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${dbName}/schema/${schema.name}`"
              >
                {{ schema.name }}
              </a>
            </td>
            <td :class="['schema-size', 'text-end', sortCriteria == 'total_bytes' ? 'fw-bold' : '']">
              {{ schema.total_size }}
            </td>
            <template v-if="schema.n_tables > 0">
              <td class="temboard-tables text-end border-start">
                <span class="badge text-bg-secondary">
                  {{ schema.n_tables }}
                </span>
                <span class="d-inline-block" style="min-width: 80px">
                  <span v-if="schema.tables_bytes" :class="[sortCriteria == 'tables_bytes' ? 'fw-bold' : '']">
                    {{ schema.tables_size }}
                  </span>
                </span>
                <small
                  style="min-width: 70px"
                  :class="[
                    'table-bloat',
                    'd-inline-block',
                    sortCriteria == 'tables_bloat_ratio' ? 'fw-bold' : 'text-muted',
                  ]"
                >
                  <template v-if="schema.tables_bloat_bytes && schema.tables_bytes">
                    Bloat: {{ schema.tables_bloat_ratio.toFixed(1) }}%
                  </template>
                </small>
              </td>
            </template>
            <td class="temboard-tables text-center text-muted border-start small" v-else>
              <em> No table </em>
            </td>
            <td class="indexes text-end border-start" v-if="schema.n_indexes > 0">
              <span class="badge text-bg-secondary">
                {{ schema.n_indexes }}
              </span>
              <span class="d-inline-block" style="min-width: 80px">
                <span v-if="schema.indexes_bytes" :class="[sortCriteria == 'indexes_bytes' ? 'fw-bold' : '']">
                  {{ schema.indexes_size }}
                </span>
              </span>
              <small
                style="min-width: 70px"
                :class="[
                  'index-bloat',
                  'd-inline-block',
                  sortCriteria == 'indexes_bloat_ratio' ? 'fw-bold' : 'text-muted',
                ]"
              >
                <template v-if="schema.indexes_bloat_bytes && schema.indexes_bytes">
                  Bloat: {{ schema.indexes_bloat_ratio.toFixed(1) }}%
                </template>
              </small>
            </td>
            <td class="indexes text-center text-muted border-start small" v-else>
              <em> No index </em>
            </td>
            <td class="temboard-toast text-end border-start">
              <span v-if="schema.toast_bytes" :class="[sortCriteria == 'toast_bytes' ? 'fw-bold' : '']">
                {{ schema.toast_size }}
              </span>
            </td>
          </tr>
          <tr v-bind:class="{ 'bg-light2': loop_index % 2 == 0 }">
            <td colspan="5" class="border-top-0">
              <size-distribution-bar
                height="7"
                :total="database.total_bytes"
                :cat1="schema.tables_size"
                :cat1raw="schema.tables_bytes"
                cat1label="Tables"
                :cat1bis="schema.tables_bloat_size"
                :cat1bisraw="schema.tables_bloat_bytes"
                cat1bislabel="Tables Bloat"
                :cat2="schema.indexes_size"
                :cat2raw="schema.indexes_bytes"
                cat2label="Indexes"
                :cat2bis="schema.indexes_bloat_size"
                :cat2bisraw="schema.indexes_bloat_bytes"
                cat2bislabel="Indexes Bloat"
                :cat3="schema.toast_size"
                :cat3raw="schema.toast_bytes"
                cat3label="Toast"
              >
              </size-distribution-bar>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
