<script setup>
import daterangepicker from "daterangepicker";
import $ from "jquery";
import * as _ from "lodash";
import moment from "moment";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import dateMath from "../../datemath.js";
import rangeUtils from "../../rangeutils.js";

const emit = defineEmits(["fromtoUpdated"]);

const router = useRouter();
const route = useRoute();

let fromPicker;
let toPicker;
const ranges = ref(rangeUtils.getRelativeTimesList());

const rootEl = ref(null);

// The raw values (examples: 'now-24h', 'Tue Sep 01 2020 10:16:00 GMT+0200')
// Interaction with parent component is done with from/to props which
// are unix timestamps
const rawFrom = ref(null);
const rawTo = ref(null);

// The values to display in the custom range from and to fields
// we don't use raw values because we may want to pick/change from and
// to in the form before applying changes
const inputFrom = ref(null);
const inputTo = ref(null);
const refreshInterval = ref(null);
const intervals = ref({
  60: "1m",
  300: "5m",
  900: "15m",
});
const isPickerOpen = ref(false);

let refreshTimeoutId;

const rawFromTo = computed(() => {
  return "" + rawFrom.value + rawTo.value;
});

const isRefreshable = computed(() => {
  return (
    (rawFrom.value && rawFrom.value.toString().indexOf("now") != -1) ||
    (rawTo.value && rawTo.value.toString().indexOf("now") != -1)
  );
});

watch(rawFromTo, () => {
  // "'' + date" will:
  //  - convert 'date' to unix timestamp (ms) if it's a moment object
  //  - not do anything if date is a string ('now - 24h' for example)
  router.push({
    path: route.path,
    query: _.assign({}, route.query, {
      start: "" + rawFrom.value,
      end: "" + rawTo.value,
    }),
  });
  inputFrom.value = rawFrom.value;
  inputTo.value = rawTo.value;
});
watch(refreshInterval, refresh);

router.afterEach((to) => {
  if (!to.query.start || !to.query.end) {
    return;
  }
  // Detect changes in browser history (back button for example)
  if (to.query.start) {
    rawFrom.value = convertTimestampToDate(to.query.start);
  }
  if (to.query.end) {
    rawTo.value = convertTimestampToDate(to.query.end);
  }
  refresh();
});

const rangeString = computed(() => {
  if (!rawFrom.value || !rawTo.value) {
    return;
  }
  return rangeUtils.describeTimeRange({
    from: rawFrom.value,
    to: rawTo.value,
  });
});

router.isReady().then(() => {
  /**
   * Parse location to get start and end date
   * If dates are not provided, falls back to the date range corresponding to
   * the last 24 hours.
   */
  const start = route.query.start || "now-24h";
  const end = route.query.end || "now";
  rawFrom.value = convertTimestampToDate(start);
  rawTo.value = convertTimestampToDate(end);
  notify();

  synchronizePickers();
});

function convertTimestampToDate(date) {
  const timestamp = parseInt(date, 10);
  return _.isFinite(timestamp) ? moment(timestamp) : date;
}

function loadRangeShortcut(shortcut) {
  rawFrom.value = shortcut.from;
  rawTo.value = shortcut.to;
  isPickerOpen.value = false;
  refresh();
}

function showHidePicker() {
  isPickerOpen.value = !isPickerOpen.value;
}

function parseInputDate(date) {
  /*
   * Tries to convert a date or string to moment
   * Returns value unchanged if not a valid date
   */
  if (moment.isMoment(date)) {
    return date;
  }
  const newDate = moment(new Date(date));
  return newDate.isValid() ? newDate : date;
}

function onApply() {
  /*
   * Called when global "apply" button is clicked
   */
  isPickerOpen.value = false;
  rawFrom.value = parseInputDate(inputFrom.value);
  rawTo.value = parseInputDate(inputTo.value);
  refresh();
}

const pickerOptions = {
  singleDatePicker: true,
  timePicker: true,
  timePicker24Hour: true,
  timePickerSeconds: false,
};

/*
 * Make sure that date pickers are up-to-date
 * especially with any 'now-like' dates
 */
function synchronizePickers() {
  // update 'from' date picker only if not currently open
  // and 'from' is updating (ie. contains 'now')
  if (!fromPicker || !fromPicker.data("daterangepicker").isShowing) {
    fromPicker = $(rootEl.value)
      .find("[data-role=from-picker]")
      .daterangepicker(
        $.extend(
          {
            startDate: dateMath.parse(rawFrom.value),
          },
          pickerOptions,
        ),
        onFromPickerApply,
      );
  }
  // update 'to' date picker only if not currently open
  // and 'to' is updating (ie. contains 'now')
  if (!toPicker || !toPicker.data("daterangepicker").isShowing) {
    toPicker = $(rootEl.value)
      .find("[data-role=to-picker]")
      .daterangepicker(
        $.extend(
          {
            startDate: dateMath.parse(rawTo.value),
            minDate: dateMath.parse(rawFrom.value),
          },
          pickerOptions,
        ),
        onToPickerApply,
      );
  }
}

function setToPickerMinDate() {
  $(rootEl.value)
    .find("[data-role=to-picker]")
    .daterangepicker(
      $.extend(
        {
          minDate: dateMath.parse(inputFrom.value),
        },
        pickerOptions,
      ),
      onToPickerApply,
    );
}

function onFromPickerApply(date) {
  inputFrom.value = date;
  setToPickerMinDate();
}

function onToPickerApply(date) {
  inputTo.value = date;
}

function refresh() {
  notify();
  clearTimeout(refreshTimeoutId);
  if (refreshInterval.value) {
    refreshTimeoutId = window.setTimeout(refresh, refreshInterval.value * 1000);
  }
}

function setFromTo(from, to) {
  rawFrom.value = from;
  rawTo.value = to;
}

defineExpose({ setFromTo });

function notify() {
  emit("fromtoUpdated", dateMath.parse(rawFrom.value), dateMath.parse(rawTo.value, true));
}
</script>

<template>
  <div v-cloak ref="rootEl">
    <button id="buttonPicker" class="btn btn-secondary" v-on:click="showHidePicker">
      <i class="fa fa-clock-o"></i>&nbsp;
      <span v-cloak>{{ rangeString }}</span>
    </button>
    <div
      class="row position-absolute bg-light border rounded card-body picker-dropdown-panel m-1 w-100 shadow"
      v-show="isPickerOpen"
      v-cloak
    >
      <div class="col-4">
        <h3>Custom range</h3>
        <form>
          <div class="form-group">
            <label for="inputFrom">From:</label>
            <div class="input-group">
              <input type="text" id="inputFrom" v-model="inputFrom" class="form-control" />
              <div class="input-group-append" data-role="from-picker">
                <div class="input-group-text">
                  <i class="fa fa-calendar"></i>
                </div>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label for="inputTo">To:</label>
            <div class="input-group">
              <input type="text" id="inputTo" v-model="inputTo" class="form-control" />
              <div class="input-group-append" data-role="to-picker">
                <div class="input-group-text">
                  <i class="fa fa-calendar"></i>
                </div>
              </div>
            </div>
          </div>
          <div>
            <button class="btn btn-primary" v-on:click.prevent="onApply">Apply</button>
          </div>
        </form>
      </div>
      <div class="col-8 pl-4">
        <h3>Quick ranges</h3>
        <div class="row">
          <ul class="list-unstyled col" v-for="section in ranges">
            <li class="shortcut" v-for="range in section">
              <a href :data-from="range.from" :data-to="range.to" v-on:click.prevent="loadRangeShortcut(range)">
                {{ rangeUtils.describeTimeRange(range) }}
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="btn-group">
      <button id="buttonRefresh" class="btn btn-secondary" v-on:click="refresh()" :disabled="!isRefreshable">
        <i class="fa fa-refresh"></i>
      </button>
      <button
        id="buttonAutoRefresh"
        type="button"
        class="btn btn-secondary dropdown-toggle"
        data-bs-toggle="dropdown"
        aria-haspopup="true"
        aria-expanded="false"
        :disabled="!isRefreshable"
      >
        <span class="text-warning" v-if="isRefreshable">
          {{ intervals[refreshInterval] }}
        </span>
      </button>
      <div class="dropdown-menu dropdown-menu-right" style="min-width: 50px">
        <a class="dropdown-item refresh-off" href v-on:click.prevent="refreshInterval = null">Off</a>
        <div class="dropdown-divider"></div>
        <a
          :class="'dropdown-item refresh-' + interval"
          href
          v-on:click.prevent="refreshInterval = key"
          v-for="(interval, key) in intervals"
          >{{ interval }}</a
        >
      </div>
    </div>
  </div>
</template>
