<script setup>
import { UseClipboard } from "@vueuse/components";
import { BTable } from "bootstrap-vue-next";
import hljs from "highlight.js/lib/core";
import sql from "highlight.js/lib/languages/sql";
import "highlight.js/styles/default.css";
import * as _ from "lodash";
import { computed, ref, watch } from "vue";

import ModalDialog from "../components/ModalDialog.vue";
import { formatDuration } from "../utils/duration";

hljs.registerLanguage("sql", sql);

let request = null;
const intervalDuration = 2;
let loadTimeout;
const activityData = ref({});

let loading = ref(false);
let terminateLoading = ref(false);
const mode = ref("running");
const paused = ref(false);
const selectedPids = ref([]);
const filter = ref(null);
const states = [
  "active",
  "idle",
  "idle in transaction",
  "idle in transaction (aborted)",
  "fastpath function call",
  "disabled",
];
const selectedStates = ref(JSON.parse(localStorage.getItem("temboardActivityStateFilters")) || states);

function load() {
  const lastLoad = new Date();

  request = $.ajax({
    url: "/proxy/" + agent_address + "/" + agent_port + "/activity",
    type: "GET",
    beforeSend: function () {
      loading.value = true;
    },
    async: true,
    contentType: "application/json",
    success: function (data) {
      clearError();
      activityData.value = data;
    },
    error: function (xhr, status) {
      if (status == "abort") {
        return;
      }
      showError(xhr);
    },
    complete: function () {
      loading.value = false;
      const timeoutDelay = intervalDuration * 1000 - (new Date() - lastLoad);
      loadTimeout = window.setTimeout(load, timeoutDelay);
    },
  });
}

// Launch once
load();

function terminate() {
  $.ajax({
    url: "/proxy/" + agent_address + "/" + agent_port + "/activity/kill",
    type: "POST",
    async: true,
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({ pids: selectedPids.value }),
    success: function () {
      $("#terminateModal").modal("hide");
      terminateLoading.value = false;
      selectedPids.value = [];
      paused.value = false;
      load();
    },
    error: function (xhr) {
      terminateLoading.value = false;
      console.log(xhr.status);
    },
  });
}

var entityMap = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
  "/": "&#x2F;",
};

function escapeHtml(string) {
  return String(string).replace(/[&<>"'\/]/g, function (s) {
    return entityMap[s];
  });
}

String.prototype.trunc =
  String.prototype.trunc ||
  function (n) {
    return this.length > n ? this.substr(0, n - 1) + "&hellip;" : this;
  };

function human2bytes(value) {
  const val = parseFloat(value);
  if (_.isFinite(val)) {
    const suffix = value.slice(-1);
    const suffixes = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"];
    return val * Math.pow(2, suffixes.indexOf(suffix) * 10);
  }
  return value;
}

function formatDurationSeconds(duration) {
  return formatDuration(duration * 1000, true);
}

function truncateState(value) {
  return value && value.trunc(12);
}

function stateClass(value) {
  if (value == "active") {
    return "text-success font-weight-bold";
  } else if (value.indexOf("idle in transaction") != -1) {
    return "text-danger font-weight-bold";
  }
}

function pause() {
  paused.value = true;
  request && request.abort();
  window.clearTimeout(loadTimeout);
}

function resume() {
  paused.value = false;
  selectedPids.value = [];
  load();
}

const filteredSessions = computed(() => {
  return _.filter(sessions.value, (session) => {
    return (
      _.includes(selectedStates.value, session.state) &&
      _.some(_.map(_.values(session), _.upperCase), (v) => _.includes(v, _.upperCase(filter.value)))
    );
  });
});

function highlight(src) {
  return hljs.highlight(src, { language: "sql" }).value;
}

const fields = computed(() => {
  let fields = [
    { label: "", key: "check" },
    { label: "PID", key: "pid", class: "text-right" },
    { label: "Database", key: "database" },
    { label: "User", key: "user", orderable: false },
    { label: "Application", key: "application_name" },
    { label: "CPU", key: "cpu", class: "text-right" },
    { label: "mem", key: "memory", class: "text-right" },
    { label: "Read/s", key: "read_s", class: "text-right", formatter: human2bytes },
    { label: "Write/s", key: "write_s", class: "text-right", formatter: human2bytes },
    { label: "IOW", key: "iow", sortable: true, class: "text-center" },
  ];

  if (mode.value == "running") {
    fields = fields.concat([{ label: "W", key: "wait", class: "text-center" }]);
  } else {
    fields = fields.concat([
      { label: "Lock Rel.", data: "relation", class: "text-right" },
      { label: "Lock Mode", key: "mode" },
      { label: "Lock Type", key: "type" },
    ]);
  }

  fields = fields.concat([
    { label: "State", key: "state", sortable: true, class: "text-center", tdClass: stateClass },
    {
      label: "Time",
      key: "duration",
      class: "text-right",
      formatter: formatDurationSeconds,
      sortable: true,
    },
    {
      label: "Query",
      key: "query",
      class: "query",
      sortable: true,
      tdAttr: {
        "data-toggle": "popover",
        "data-trigger": "hover",
      },
    },
  ]);
  return fields;
});

const freezed = computed(() => selectedPids.value.length > 0);

const sessions = computed(() => {
  return activityData.value[mode.value] ? activityData.value[mode.value].rows : [];
});

const waitingCount = computed(() => {
  return activityData.value["waiting"] ? activityData.value["waiting"].rows.length : undefined;
});

const blockingCount = computed(() => {
  return activityData.value["blocking"] ? activityData.value["blocking"].rows.length : undefined;
});

watch(selectedStates, (val) => {
  localStorage.setItem("temboardActivityStateFilters", JSON.stringify(val));
});

function reset() {
  terminateLoading.value = undefined;
}
</script>

<template>
  <div>
    <!-- Mode Tabs -->
    <ul class="nav nav-tabs">
      <li class="nav-item">
        <a href="#" :class="{ active: mode == 'running' }" class="nav-link running" @click.prevent="mode = 'running'">
          Running</a
        >
      </li>
      <li class="nav-item">
        <a href="#" :class="{ active: mode == 'waiting' }" class="nav-link waiting" @click.prevent="mode = 'waiting'">
          Waiting
          <div
            id="waiting-count"
            class="badge"
            :class="waitingCount > 0 ? 'badge-warning' : 'badge-light'"
            style="min-width: 2em"
          >
            {{ waitingCount || "&nbsp;" }}
          </div>
        </a>
      </li>
      <li class="nav-item">
        <a href="#" :class="{ active: mode == 'blocking' }" class="nav-link blocking" @click.prevent="mode = 'blocking'"
          >Blocking
          <div
            id="blocking-count"
            class="badge"
            :class="blockingCount > 0 ? 'badge-warning' : 'badge-light'"
            style="min-width: 2em"
          >
            {{ blockingCount || "&nbsp;" }}
          </div>
        </a>
      </li>
    </ul>
    <div class="row d-flex justify-content-between">
      <div class="col-auto">
        <span class="d-inline-block" data-toggle="tooltip" title="Terminate the backends selected below">
          <button
            id="killButton"
            type="button"
            class="btn btn-danger"
            :class="{ disabled: !freezed }"
            data-toggle="modal"
            data-target="#terminateModal"
          >
            Terminate
          </button>
        </span>
      </div>
      <div class="col-auto align-self-center">
        <span id="autoRefreshResume" class="d-text-muted" :class="{ 'd-none': !freezed }">
          <a class="btn btn-secondary" role="button" href @click.prevent="resume"
            ><i class="fa fa-play"></i> resume auto refresh</a
          >
        </span>
        <span class="text-muted" :class="{ 'd-none': freezed }">
          <img src="/images/ring-alt.svg" width="24" class="fa-fw" :class="{ 'd-none': !loading }" />
          Auto refresh
          <span :class="{ 'd-none': paused }">2s</span>
          <span :class="{ 'd-none': !paused }">paused</span>
        </span>
      </div>
      <div class="col-auto">
        <a
          class="btn collapse-toggle dropdown-toggle collapsed"
          data-toggle="collapse"
          href="#filters"
          role="button"
          aria-expanded="false"
          aria-controls="filters"
        >
          filters
        </a>
      </div>
    </div>
    <!-- Filters drop down -->
    <div class="row">
      <div class="col-12 collapse" id="filters">
        <div class="justify-content-end d-flex">
          <div class="form-group mb-1">
            <input type="text" placeholder="Search" class="form-control" v-model="filter" />
          </div>
        </div>
        <form id="state-filter" class="form-inline justify-content-end d-flex">
          <div class="form-group pr-1">
            <label><strong>States:</strong></label>
          </div>

          <div class="form-check form-check-inline" v-for="state in states">
            <input
              class="form-check-input"
              type="checkbox"
              :id="`state-filter-${state}`"
              :value="state"
              checked
              v-model="selectedStates"
            />
            <label class="form-check-label" :for="`state-filter-${state}`">{{ state }}</label>
          </div>
        </form>
      </div>
    </div>
    <!-- Sessions table -->
    <div class="row">
      <div class="col-12">
        <BTable
          striped
          small
          :items="filteredSessions"
          :fields="fields"
          class="table-query mt-1 small"
          @row-hovered="pause"
          @row-unhovered="!freezed && resume()"
          sort-by="duration"
          sort-desc
        >
          <template v-slot:cell()="data">
            <span v-html="data.value" :class="{ 'text-danger font-weight-bold': data.value == 'Y' }"></span>
          </template>
          <template v-slot:cell(check)="row">
            <input
              type="checkbox"
              :disabled="!paused && !freezed"
              class="input-xs"
              v-model="selectedPids"
              :value="row.item.pid"
              title="Select to terminate"
            />
          </template>
          <template v-slot:cell(query)="data">
            <div class="position-relative clipboard-parent">
              <UseClipboard v-slot="{ copy, copied }" :legacy="true">
                <span
                  class="copy invisible position-absolute top-0 right-0 pr-1 pl-1 bg-secondary text-white rounded"
                  title="Copy to clipboard"
                  @click="copy(data.item.query)"
                >
                  {{ copied ? "Copied" : "Copy" }}
                </span>
              </UseClipboard>
              <pre class="sql hljs" v-html="highlight(data.value)"></pre>
            </div>
          </template>
          <template v-slot:cell(state)="data">
            <span :title="data.value" v-html="truncateState(data.value)"></span>
          </template>
        </BTable>
        <p class="text-center text-muted">Showing 300 longest queries.</p>
      </div>
    </div>
    <ModalDialog id="terminateModal" title="Terminate Backend" v-on:closed="reset">
      <div class="modal-body">
        Please confirm you want to terminated the following backend PIDs:
        <span class="badge badge-primary" v-for="pid in selectedPids">{{ pid }}</span>
      </div>

      <div class="modal-body">
        <div class="row" v-if="terminateLoading">
          <div class="col-4 offset-4">
            <div class="progress">
              <div class="progress-bar progress-bar-striped" style="width: 100%">Please wait ...</div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button id="submitKill" type="button" class="btn btn-danger" :disabled="terminateLoading" @click="terminate">
          Yes, terminate
        </button>
        <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>
      </div>
    </ModalDialog>
  </div>
</template>

<style scoped>
.clipboard-parent:hover .copy {
  visibility: visible !important;
}
</style>
