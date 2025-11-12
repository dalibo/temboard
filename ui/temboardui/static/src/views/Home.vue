<script setup>
// Global: clearError, showError
import { useFullscreen } from "@vueuse/core";
import { Popover, Tooltip } from "bootstrap";
import $ from "jquery";
import _ from "lodash";
import moment from "moment";
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import InstanceCard from "../components/home/InstanceCard.vue";

const root = ref(null);
const instanceCards = ref(null);
const route = useRoute();
const router = useRouter();

const loading = ref(false);
const instances = ref([]);
const search = ref(route.query.q);
const sort = ref(route.query.sort || "status");
const environmentsFilter = ref(route.query.environments ? route.query.environments.split(",") : []);
const start = ref(moment().subtract(1, "hours"));
const end = ref(moment());
const refreshDate = ref(null);
const refreshInterval = ref(3 * 1000);
let popoverList = [];
let tooltipList = [];

// Pagination variables
const currentPage = ref(1);
const rowsPerPage = ref(4);
// Initial value cannot be null or 0, otherwise itemsPerPage will fail at first load
const colsPerRow = ref(1);

const totalPages = computed(() => {
  return Math.ceil(filteredInstances.value.length / itemsPerPage.value) || 1;
});

const { toggle } = useFullscreen(root);

const props = defineProps(["isAdmin", "environments"]);

const filteredInstances = computed(() => {
  const searchRegex = new RegExp(search.value, "i");
  const filtered = instances.value.filter((instance) => {
    return (
      searchRegex.test(instance.hostname) ||
      searchRegex.test(instance.agent_address) ||
      searchRegex.test(instance.pg_data) ||
      searchRegex.test(instance.pg_port) ||
      searchRegex.test(instance.pg_version) ||
      searchRegex.test(instance.environment)
    );
  });
  let sorted;
  if (sort.value == "status") {
    sorted = sortByStatus(filtered);
  } else {
    sorted = _.sortBy(filtered, sort.value, "asc");
  }

  return sorted.filter((instance) => {
    if (!environmentsFilter.value.length) {
      return true;
    }
    return environmentsFilter.value.indexOf(instance.environment) != -1;
  });
});

const paginatedInstances = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value;
  const end = start + itemsPerPage.value;
  return filteredInstances.value.slice(start, end);
});

onMounted(() => {
  refreshCards();
  window.setInterval(refreshCards, refreshInterval.value);
  nextTick(() => {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map((el) => new Tooltip(el, { sanitize: false }));
  });
  window.addEventListener("resize", handleResize);

  const savedRowsPerPage = localStorage.getItem("rowsPerPage");
  if (savedRowsPerPage) {
    rowsPerPage.value = savedRowsPerPage;
  }
  updatePagination();
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
});

function toggleEnvironmentFilter(environment, e) {
  e.preventDefault();
  var index = environmentsFilter.value.indexOf(environment);
  if (index != -1) {
    environmentsFilter.value.splice(index, 1);
  } else {
    environmentsFilter.value.push(environment);
  }
}
function changeSort(value, e) {
  e.preventDefault();
  sort.value = value;
}

function fetchInstances() {
  clearError();
  $.ajax("/json/instances/home")
    .done((data) => {
      popoverList.forEach((p) => p.dispose());
      tooltipList.forEach((t) => t.dispose());
      instances.value = data;
      nextTick(() => {
        const popoverTriggerList = root.value.querySelectorAll('[data-bs-toggle="popover"]');
        popoverList = [...popoverTriggerList].map((el) => new Popover(el, { sanitize: false }));
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipList = [...tooltipTriggerList].map((el) => new Tooltip(el, { sanitize: false }));
      });
    })
    .fail((xhr) => {
      showError(xhr);
    });
}

function refreshCards() {
  loading.value = true;
  fetchInstances();
  end.value = moment();
  start.value = moment().subtract(1, "hours");
  nextTick(() => {
    for (let i in instanceCards.value) {
      const card = instanceCards.value[i];
      if (i >= 18) {
        break;
      }
      card.fetchLoad1();
      card.fetchTPS();
    }
    refreshDate.value = moment();
    loading.value = false;
  });
}

function sortByStatus(items) {
  return items.sort(function (a, b) {
    return getStatusValue(b) - getStatusValue(a);
  });
}

/*
 * Util to compute a global status value given an instance
 */
function getStatusValue(instance) {
  var checks = getChecksCount(instance);
  var value = 0;
  if (checks.CRITICAL) {
    value += checks.CRITICAL * 1000000;
  }
  if (checks.WARNING) {
    value += checks.WARNING * 1000;
  }
  if (checks.UNDEF) {
    value += checks.UNDEF;
  }
  return value;
}

function getChecksCount(instance) {
  var count = _.countBy(
    instance.checks.map(function (state) {
      return state.state;
    }),
  );
  return count;
}

watch(search, (newVal) => {
  router.replace({
    query: _.assign({}, route.query, { q: newVal }),
  });
});
watch(sort, (newVal) => {
  router.replace({
    query: _.assign({}, route.query, { sort: newVal }),
  });
});
watch(environmentsFilter.value, (newVal) => {
  router.replace({
    query: _.assign({}, route.query, { environments: newVal.join(",") }),
  });
});

// Watch changes in filters and reset current page. This prevents empty pages.
watch(
  () => [search.value, environmentsFilter.value],
  (newVal) => {
    currentPage.value = 1;
  },
  { deep: true },
);

function getColumnsPerRow() {
  const container = document.querySelector("#cards");
  const children = [...container.children];
  if (children.length === 0) return 0;

  // Measure the top offset — items in the same row have the same offsetTop
  const firstOffset = children[0].offsetTop;

  // Count how many items share the same offsetTop as the first
  return children.filter((c) => c.offsetTop === firstOffset).length;
}

// Calculate how many items fit on one row
function updatePagination() {
  colsPerRow.value = getColumnsPerRow();
}

const itemsPerPage = computed(() => colsPerRow.value * rowsPerPage.value);

// Watch for resize or zoom (zoom triggers resize in most browsers)
function handleResize() {
  nextTick(updatePagination);
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
}
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
}
function goToPage(page) {
  currentPage.value = page;
}

watch(rowsPerPage, (newValue) => {
  localStorage.setItem("rowsPerPage", newValue);
});

watch(totalPages, (newValue) => {
  // Make sure current page is not out of range
  currentPage.value = Math.min(currentPage.value, newValue);
});
</script>

<template>
  <div ref="root">
    <div class="position-absolute" style="z-index: 2; right: 0">
      <button id="fullscreen" class="btn btn-link" @click="toggle">
        <i class="fa fa-expand"></i>
      </button>
    </div>
    <div class="row mb-2">
      <div class="col d-flex">
        <input type="text" class="form-control me-sm-2 w-auto" placeholder="Search instances" v-model="search" />
        <div class="dropdown me-sm-2">
          <button type="button" class="btn btn-secondary dropdown-toggle" data-bs-toggle="dropdown">
            Sort by: <strong v-cloak>{{ sort }}</strong>
            <span class="caret"></span>
          </button>
          <div class="dropdown-menu" role="menu">
            <a class="dropdown-item" href v-on:click="changeSort('hostname', $event)">
              <i v-bind:class="['fa fa-fw', { 'fa-check': sort == 'hostname' }]"></i>
              Hostname
            </a>
            <a class="dropdown-item" href v-on:click="changeSort('status', $event)">
              <i v-bind:class="['fa fa-fw', { 'fa-check': sort == 'status' }]"></i>
              Status
            </a>
          </div>
        </div>
        <div class="dropdown" v-if="environments.length > 1">
          <button type="button" class="btn btn-secondary dropdown-toggle" data-bs-toggle="dropdown">
            Environments ({{ environmentsFilter.length || "all" }})
            <span class="caret"></span>
          </button>
          <div class="dropdown-menu" role="menu">
            <a
              class="dropdown-item"
              href="#"
              v-for="environment in environments"
              v-on:click="toggleEnvironmentFilter(environment, $event)"
            >
              <i v-bind:class="['fa fa-fw', { 'fa-check': environmentsFilter.indexOf(environment) != -1 }]"></i>
              {{ environment }}
            </a>
          </div>
        </div>
      </div>
      <div class="col text-center" v-if="environments.length === 1">
        <span
          class="lead"
          v-bind:title="'Showing instances of environment ' + environments[0]"
          data-bs-toggle="tooltip"
          >{{ environments[0] }}</span
        >
      </div>
      <div class="col">
        <p class="text-secondary text-end mt-2 mb-0 me-4">
          <i v-if="loading" class="fa fa-spinner fa-spin loader"></i>
          <span :title="refreshDate ? 'last refresh at ' + refreshDate.format('HH:mm:ss') : ''"
            >Refreshed every 1m</span
          >
        </p>
      </div>
    </div>
    <div class="d-flex justify-content-end align-items-center mb-2">
      <div class="d-flex align-items-center me-2">
        <label for="rowsPerPage" class="form-label text-nowrap me-2 mb-0">Rows per page:</label>
        <input
          type="number"
          class="form-control form-control-sm"
          id="rowsPerPage"
          min="1"
          max="9"
          v-model="rowsPerPage"
        />
      </div>
      <nav>
        <ul class="pagination pagination-sm mb-0">
          <li class="page-item" :class="{ disabled: currentPage === 1 }">
            <a class="page-link" href="#" @click="prevPage" aria-label="Previous">
              <span aria-hidden="true">&laquo;</span>
              <span class="sr-only">Previous</span>
            </a>
          </li>
          <li
            class="page-item"
            v-for="page in Array.from({ length: totalPages }, (_, i) => i + 1)"
            :key="page"
            :class="{ active: page === currentPage }"
            @click="goToPage(page)"
          >
            <a class="page-link" href="#">{{ page }}</a>
          </li>
          <li class="page-item" :class="{ disabled: currentPage === totalPages }">
            <a class="page-link" href="#" @click="nextPage" aria-labal="Next">
              <span aria-hidden="true">&raquo;</span>
              <span class="sr-only">Next</span>
            </a>
          </li>
        </ul>
      </nav>
    </div>

    <!-- Extra hidden row to compute number of columns  -->
    <div class="row" id="cards" style="visibility: hidden; height: 0">
      <div v-for="i in Array(12)" ref="cards" class="col-xs-12 col-sm-6 col-md-4 col-lg-3 col-xl-2 pb-3"></div>
    </div>

    <div class="row">
      <div
        v-for="instance in paginatedInstances"
        :key="instance.hostname + instance.pg_port"
        ref="cards"
        v-cloak
        class="col-xs-12 col-sm-6 col-md-4 col-lg-3 col-xl-2 pb-3"
      >
        <InstanceCard
          v-bind:instance="instance"
          v-bind:status_value="getStatusValue(instance)"
          v-bind:refreshInterval="refreshInterval"
          v-bind:start="start"
          v-bind:end="end"
          ref="instanceCards"
        ></InstanceCard>
      </div>
    </div>
    <div v-if="!loading && instances.length == 0" class="row justify-content-center" v-cloak>
      <div class="col col-12 col-sm-10 col-md-6 col-lg-4 text-body-secondary text-center">
        <h4 class="m-4">No instance</h4>
        <template v-if="isAdmin">
          <p>No instance is available yet.</p>
          <p>
            Go to
            <strong><a href="/settings/instances">Settings</a></strong> to add or configure instances.
          </p>
        </template>
        <template v-if="!isAdmin">
          <p>You don't have access to any instance.</p>
          <p>Please contact an administrator.</p>
        </template>
      </div>
    </div>
  </div>
</template>
