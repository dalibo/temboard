<script setup>
import $ from "jquery";
import * as _ from "lodash";
import { ref } from "vue";

import { stateBgClass, stateBorderClass, stateIcon } from "../utils/state";

const checks = ref([]);

function sorted(items, key) {
  return _.orderBy(items, key);
}

function refresh() {
  $.ajax({
    url: apiUrl + "/checks.json",
    success: function (data) {
      checks.value = data;
    },
    error: function (error) {
      console.error(error);
    },
  });
}

// refresh every 1 min
window.setInterval(function () {
  refresh();
}, 60 * 1000);
refresh();
</script>
<template>
  <div>
    <div class="text-end text-body-secondary small">Auto refresh every 1 min</div>
    <div id="checks-container" class="row" v-cloak>
      <template v-for="check in checks">
        <div class="col-3" v-if="check.state != 'UNDEF'">
          <div
            v-bind:id="'status-' + check.name"
            class="card mb-3 w-100 border"
            v-bind:class="[stateBorderClass(check.state), { 'striped bg-light': !check.enabled }]"
          >
            <div class="card-body p-2">
              <div>
                <a v-bind:href="'alerting/' + check.name" v-bind:class="{ 'text-body-secondary': !check.enabled }">
                  <span class="badge" v-bind:class="stateBgClass(check.state)">
                    <i class="fa fa-fw" :class="[stateIcon(check.state)]"></i>
                    {{ check.state }}</span
                  >
                  {{ check.description }}
                </a>
              </div>
              <hr class="mt-1 mb-1" />
              <ul class="list-unstyled small ms-2 mb-0" style="max-height: 100px; overflow-y: auto">
                <li v-for="key in sorted(check.state_by_key, 'key')">
                  <span class="badge" v-bind:class="stateBgClass(key.state)">
                    <i class="fa fa-fw" :class="[stateIcon(key.state)]"></i>
                    {{ key.state }}</span
                  >
                  {{ key.key }}
                </li>
              </ul>
              <hr class="mt-1 mb-1" />
              <div>
                <ul class="list-inline small text-body-secondary mb-0">
                  <li class="list-inline-item">
                    Warning: {{ check.warning }}{{ check.value_type == "percent" ? "%" : "" }}
                  </li>
                  <li class="list-inline-item">
                    Critical: {{ check.critical }}{{ check.value_type == "percent" ? "%" : "" }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
