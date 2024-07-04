<script setup>
import $ from "jquery";
import { computed, provide, ref } from "vue";

import AlertingChart from "../components/AlertingChart.vue";
import DateRangePicker from "../components/DateRangePicker/DateRangePicker.vue";

const check = ref(window.checkInitialData);
const keys = ref([]);
const from = ref(null);
const to = ref(null);
const dateRangePickerEl = ref(null);

const sortedKeys = computed(() => {
  return keys.value.sort(function (a, b) {
    return a.key > b.key;
  });
});

$.ajax({
  url: apiUrl + "/states/" + checkInitialData.name + ".json",
  success: function (data) {
    keys.value = data;
  },
  error: function (error) {
    console.error(error);
  },
});

function setFromTo(from, to) {
  dateRangePickerEl.value.setFromTo(from, to);
}

provide("setFromTo", setFromTo);

function onFromToUpdate(from_, to_) {
  from.value = from_;
  to.value = to_;
}
</script>

<template>
  <div id="check-container" v-cloak>
    <div class="row mb-3 mb-2">
      <div class="col-12 d-flex justify-content-between">
        <ol class="breadcrumb py-1 mb-0 align-items-center">
          <li class="breadcrumb-item"><a href="../alerting">Status</a></li>
          <li class="breadcrumb-item active" aria-current="page">{{ check.description }}</li>
        </ol>
        <DateRangePicker @fromto-updated="onFromToUpdate" ref="dateRangePickerEl"></DateRangePicker>
      </div>
    </div>

    <div>
      <ul class="list-inline small text-body-secondary mb-0">
        <li class="list-inline-item">Enabled: <i :class="['fa', check['enabled'] ? 'fa-check' : 'fa-times']"></i></li>
        <li class="list-inline-item">
          <span class="text-warning"> &horbar; </span>
          Warning: {{ check.warning }}
          <template v-if="check.valueType == 'percent'">%</template>
        </li>
        <li class="list-inline-item">
          <span class="text-critical"> &horbar; </span>
          Critical: {{ check.critical }}
          <template v-if="check.valueType == 'percent'">%</template>
        </li>
        <li class="list-inline-item">
          <a data-bs-toggle="modal" data-bs-target="#updateModal" href> Edit </a>
        </li>
      </ul>

      <!-- Modal -->
      <div
        class="modal fade"
        id="updateModal"
        tabindex="-1"
        role="dialog"
        aria-labelledby="updateModalLabel"
        aria-hidden="true"
      >
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="updateModalLabel">Edit alert</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <div id="modalInfo"></div>
              <form id="updateForm">
                <div class="mb-3">
                  <label for="descriptionInput" class="form-label">Name</label>
                  <input type="text" class="form-control" id="descriptionInput" :value="check.description" />
                </div>
                <hr />

                <div class="mb-3 form-check">
                  <input type="checkbox" class="form-check-input" id="enabledInput" :checked="check.enabled" />
                  <label class="form-check-label" for="enabledInput">Enabled</label>
                  <small class="form-text text-body-secondary">
                    If disabled, no check will be made. Thus no alert will be raised.
                  </small>
                </div>
                <div class="mb-3">
                  <label for="warningThresholdInput" class="form-label">Warning threshold</label>
                  <input type="text" class="form-control" id="warningThresholdInput" :value="check.warning" />
                </div>
                <div class="mb-3">
                  <label for="criticalThresholdInput" class="form-label">Critical threshold</label>
                  <input type="text" class="form-control" id="criticalThresholdInput" :value="check.critical" />
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <i class="fa fa-spinner fa-spin loader d-none"></i>
              <button type="submit" id="submitFormUpdateCheck" class="btn btn-success ms-auto">Save</button>
              <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card w-100 mb-2" v-for="key in sortedKeys">
      <div class="p-2">
        <div class="text-center">
          <i
            v-bind:class="'fa fa-heart text-' + key.state.toLowerCase()"
            data-bs-toggle="tooltip"
            v-bind:title="'Current status: ' + key.state.toLowerCase()"
          ></i
          >&nbsp;
          <span v-if="key.key != ''">{{ key.key }}</span>
          <span v-if="key.key == ''">{{ check["name"] }}</span>
        </div>
      </div>
      <div class="card-body pt-0">
        <div :id="'legend' + key.key" class="legend-chart">
          <div class="row">
            <div class="col-md-4 col-md-offset-4">
              <div class="progress">
                <div class="progress-bar progress-bar-striped" style="width: 100%">Loading, please wait ...</div>
              </div>
            </div>
          </div>
        </div>
        <AlertingChart
          :check="check['name']"
          :key_="key.key"
          :value-type="key.value_type"
          :from="from"
          :to="to"
        ></AlertingChart>
      </div>
    </div>
  </div>
</template>
