<script setup>
import $ from "jquery";
import _ from "lodash";
import { computed, ref } from "vue";

import SizeDistributionBar from "../../components/maintenance/SizeDistributionBar.vue";

const props = defineProps(["apiUrl", "instance"]);
const total_bytes = ref(0);
const total_size = ref(0);
const databases = ref([]);
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

const databasesSorted = computed(() => {
  const sortOrder = sortCriterias.value[sortCriteria.value][1];
  return _.orderBy(databases.value, sortCriteria.value, sortOrder);
});

function fetchData() {
  $.ajax({
    url: props.apiUrl,
    contentType: "application/json",
    success: function (data) {
      total_bytes.value = data.instance.total_bytes;
      total_size.value = data.instance.total_size;
      databases.value = data.databases;

      databases.value.forEach(function (database) {
        database.tables_bloat_ratio = 0;
        if (database.tables_bytes) {
          database.tables_bloat_ratio = parseFloat(
            (100 * (database.tables_bloat_bytes / database.tables_bytes)).toFixed(1),
          );
        }
        database.indexes_bloat_ratio = 0;
        if (database.indexes_bytes) {
          database.indexes_bloat_ratio = parseFloat(
            (100 * (database.indexes_bloat_bytes / database.indexes_bytes)).toFixed(1),
          );
        }
      });
      window.setTimeout(() => {
        $('[data-bs-toggle="popover"]').popover();
      }, 1);
    },
    error: showError,
    complete: function () {
      loading.value = false;
    },
  });
}

fetchData();
</script>

<template>
  <div>
    <h3 class="row">
      <div class="col text-end" v-cloak v-if="!loading">
        Size: <strong>{{ total_size }}</strong>
      </div>
    </h3>
    <div class="text-center" v-if="loading">
      <img src="/images/ring-alt.svg" class="fa-fw fa-2x" />
    </div>
    <div v-cloak v-if="!loading">
      <div class="d-flex">
        <h4>
          Databases <span class="text-muted small">({{ databases.length }})</span>
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
        <template v-for="(database, loop_index) in databasesSorted">
          <tr v-bind:class="{ 'bg-light2': loop_index % 2 == 0 }">
            <td class="database fw-bold">
              <a :href="`/server/${instance.agentAddress}/${instance.agentPort}/maintenance/${database.datname}`">
                {{ database.datname }}
              </a>
            </td>
            <td :class="['database-size', 'text-end', sortCriteria == 'total_bytes' ? 'fw-bold' : '']">
              {{ database.total_size }}
            </td>
            <template v-if="database.n_tables > 0">
              <td class="temboard-tables text-end border-start">
                <span class="badge badge-secondary">
                  {{ database.n_tables }}
                </span>
                <span class="d-inline-block" style="min-width: 80px">
                  <span v-if="database.tables_bytes" :class="[sortCriteria == 'tables_bytes' ? 'fw-bold' : '']">
                    {{ database.tables_size }}
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
                  <template v-if="database.tables_bloat_bytes && database.tables_bytes">
                    Bloat: {{ database.tables_bloat_ratio.toFixed(1) }}%
                  </template>
                </small>
              </td>
            </template>
            <td class="temboard-tables text-center text-muted border-start small" v-else>
              <em> No table </em>
            </td>
            <td class="indexes text-end border-start" v-if="database.n_indexes > 0">
              <span class="badge badge-secondary">
                {{ database.n_indexes }}
              </span>
              <span class="d-inline-block" style="min-width: 80px">
                <span v-if="database.indexes_bytes" :class="[sortCriteria == 'indexes_bytes' ? 'fw-bold' : '']">
                  {{ database.indexes_size }}
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
                <template v-if="database.indexes_bloat_bytes && database.indexes_bytes">
                  Bloat: {{ database.indexes_bloat_ratio.toFixed(1) }}%
                </template>
              </small>
            </td>
            <td class="indexes text-center text-muted border-start small" v-else>
              <em> No index </em>
            </td>
            <td class="temboard-toast text-end border-start">
              <span v-if="database.toast_bytes" :class="[sortCriteria == 'toast_bytes' ? 'fw-bold' : '']">
                {{ database.toast_size }}
              </span>
            </td>
          </tr>
          <tr v-bind:class="{ 'bg-light2': loop_index % 2 == 0 }">
            <td colspan="5" class="border-top-0">
              <SizeDistributionBar
                height="7"
                :total="total_bytes"
                :cat1="database.tables_size"
                :cat1raw="database.tables_bytes"
                cat1label="Tables"
                :cat1bis="database.tables_bloat_size"
                :cat1bisraw="database.tables_bloat_bytes"
                cat1bislabel="Tables Bloat"
                :cat2="database.indexes_size"
                :cat2raw="database.indexes_bytes"
                cat2label="Indexes"
                :cat2bis="database.indexes_bloat_size"
                :cat2bisraw="database.indexes_bloat_bytes"
                cat2bislabel="Indexes Bloat"
                :cat3="database.toast_size"
                :cat3raw="database.toast_bytes"
                cat3label="Toast"
              >
              </SizeDistributionBar>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
