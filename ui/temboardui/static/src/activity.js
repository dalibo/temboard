import Vue from "vue";
import { ref } from "vue";
import { formatDuration } from "./utils/duration";
import BootstrapVue from "bootstrap-vue";
import "bootstrap-vue/dist/bootstrap-vue.css";
import Copy from "./copy.vue";
import * as _ from "lodash";
import hljs from "highlight.js";
import "highlight.js/styles/default.css";

Vue.use(BootstrapVue);

let request = null;
const intervalDuration = 2;
let loadTimeout;

let loading = ref(false);
const sessions = ref([]);
const waitingCount = ref(0);
const blockingCount = ref(0);
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
    beforeSend: function (xhr) {
      loading.value = true;
    },
    async: true,
    contentType: "application/json",
    success: function (data) {
      clearError();
      sessions.value = data[activityMode].rows;
      waitingCount.value = data["waiting"].rows.length;
      blockingCount.value = data["blocking"].rows.length;
    },
    error: function (xhr, status) {
      if (status == "abort") {
        return;
      }
      showError(xhr);
    },
    complete: function (xhr, status) {
      loading.value = false;
      const timeoutDelay = intervalDuration * 1000 - (new Date() - lastLoad);
      loadTimeout = window.setTimeout(load, timeoutDelay);
    },
  });
}

// Launch once
load();

function terminate(pids) {
  $("#Modal").modal("show");
  $("#ModalLabel").html("Terminate backend");
  var pids_html = "";
  for (var i = 0; i < pids.length; i++) {
    pids_html += '<span class="badge badge-primary">' + pids[i] + "</span> ";
  }
  $("#ModalInfo").html("Please confirm you want to terminated the following backend PIDs: " + pids_html);
  var footer_html = "";
  footer_html += '<button type="button" id="submitKill" class="btn btn-danger">Yes, terminate</button>';
  footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
  $("#ModalFooter").html(footer_html);
  $("#submitKill").click(function () {
    $.ajax({
      url: "/proxy/" + agent_address + "/" + agent_port + "/activity/kill",
      type: "POST",
      beforeSend: function (xhr) {
        xhr.setRequestHeader("X-Session", xsession);
        $("#ModalInfo").html(
          '<div class="row"><div class="col-4 offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>',
        );
      },
      async: true,
      contentType: "application/json",
      dataType: "json",
      data: JSON.stringify({ pids: pids }),
      success: function (data) {
        $("#Modal").modal("hide");
        var url = window.location.href;
        window.location.replace(url);
      },
      error: function (xhr) {
        console.log(xhr.status);
        // 406 is for malformed X-Session.
        if (xhr.status == 401 || xhr.status == 406) {
          var params = $.param({ redirect_to: window.location.href });
          var info = "";
          info += '<div class="row">';
          info += '  <div class="col-12">';
          info +=
            '    <div class="alert alert-danger" role="alert">Agent login required: ' +
            escapeHtml(JSON.parse(xhr.responseText).error) +
            "</div>";
          info +=
            '    <p>Go to <a href="' +
            agentLoginUrl +
            "?" +
            params +
            '">Agent Login form</a> and try again to terminate backend.</div>';
          info += "  </div>";
          info += "</div>";
          // Reuse Info dialog to avoid flicker while closing info and opening error.
          $("#ModalInfo").html(info);
          $("#ModalFooter").html(
            '<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>',
          );
        } else {
          $("#ModalInfo").html(
            '<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert">Error: ' +
              escapeHtml(JSON.parse(xhr.responseText).error) +
              "</div></div></div>",
          );
          $("#ModalFooter").html(
            '<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>',
          );
        }
      },
    });
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

function stateClass(value, key, item) {
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

function doFilter(row) {
  return (
    _.includes(selectedStates.value, row.state) &&
    _.some(_.map(_.values(row), _.upperCase), (v) => _.includes(v, _.upperCase(filter.value)))
  );
}

function highlight(src) {
  return hljs.highlight("sql", src).value;
}
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

if (activityMode == "running") {
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

new Vue({
  el: "#app",
  data: {
    blockingCount,
    fields,
    filter,
    states,
    paused,
    selectedStates,
    selectedPids,
    sessions,
    waitingCount,
    loading,
  },
  methods: {
    doFilter,
    highlight,
    pause,
    resume,
    terminate,
    truncateState,
  },
  computed: {
    freezed: () => selectedPids.value.length > 0,
  },
  watch: {
    selectedStates: function (val) {
      localStorage.setItem("temboardActivityStateFilters", JSON.stringify(val));
    },
  },
  components: {
    copy: Copy,
  },
});
