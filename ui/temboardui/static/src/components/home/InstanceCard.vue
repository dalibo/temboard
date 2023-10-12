<script type="text/javascript">
import _ from "lodash";
import Dygraph from "dygraphs";
import "dygraphs/dist/dygraph.css";

import Checks from "./Checks.vue";
import Sparkline from "./Sparkline.vue";

export default {
  data: function () {
    return {
      load1_data: null,
      load1_last: "N/A",
      tps_data: null,
      tps_last: "N/A",
    };
  },
  computed: {
    dashboard_url: function () {
      return ["/server", this.instance.agent_address, this.instance.agent_port, "dashboard"].join("/");
    },
    hasMonitoring: function () {
      return this.instance.plugins.indexOf("monitoring") != -1;
    },
  },
  props: ["end", "index", "refreshInterval", "start", "status_value", "instance"],
  components: {
    checks: Checks,
    sparkline: Sparkline,
  },
  mounted: function () {
    if (this.index >= 18) {
      return;
    }

    this.fetchTPS();
    this.fetchLoad1();
  },
  watch: {
    index: function () {
      if (this.index >= 18) {
        this.load1_data = null;
        this.load1_last = null;
        this.tps_data = null;
        this.tps_last = null;
      }
    },
  },
  methods: {
    fetchLoad1: function () {
      this.fetchMetric("load1").done((data) => {
        if (data) {
          this.load1_data = data;
        }
      });
    },
    fetchTPS: function () {
      this.fetchMetric("tps").done((data) => {
        if (data) {
          this.tps_data = data;
        }
      });
    },
    fetchMetric: function (metric) {
      var url = ["/server", this.instance.agent_address, this.instance.agent_port, "monitoring/data", metric].join("/");
      var params = "?start=" + this.start.toISOString() + "&end=" + this.end.toISOString();
      return $.get(url + params);
    },
    setLastLoad1: function (last_value) {
      // Use Dygraphs to parse CSV and report last point in VueJS context.
      this.load1_last = last_value || "N/A";
    },
    setLastTPS: function (last_value) {
      // Use Dygraphs to parse CSV and report last point in VueJS context.
      this.tps_last = last_value || "N/A";
    },
  },
};
</script>

<template>
  <div
    :class="[
      'card',
      {
        'border-danger bg-danger-light': status_value >= 1000000,
        'border-warning bg-warning-light': status_value >= 1000,
      },
    ]"
  >
    <div class="card-body p-2" style="min-height: 150px">
      <div class="row">
        <div class="col-md-12">
          <p class="mb-0 overflow-ellipsis">
            <strong>
              <i class="fa fa-database"></i>
              <a
                :href="dashboard_url"
                :title="
                  instance.pg_version_summary + ' listening on ' + [instance.hostname, instance.pg_port].join(':')
                "
                class="instance-link"
                data-toggle="tooltip"
              >
                {{ instance.hostname }}:{{ instance.pg_port }}
              </a>
            </strong>
          </p>
          <p class="mb-0 small">
            <template v-for="(group, index) in instance.groups">
              <span class="badge border text-muted mr-1" :title="'Instance in group ' + group">
                {{ group }}
              </span>
            </template>
            <span class="pg_version">{{ instance.pg_version_summary || "Unknown version" }}</span>
          </p>
          <checks :instance="instance"></checks>
        </div>
      </div>
      <!-- Limit graph to top 3 rows. -->
      <div class="row" v-if="hasMonitoring && index < 18">
        <div class="col-md-6 mt-2 small text-center">
          <span class="text-muted" v-if="tps_last"> TPS: </span>
          <span class="badge badge-secondary" v-if="tps_last">
            {{ tps_last }}
          </span>
          <sparkline
            :data="tps_data"
            :start="start"
            :end="end"
            :colors="['#50BD68', '#F15854']"
            @chart-rendered="setLastTPS"
            ref="tps_chart"
            class="sparkline-container"
            data-toggle="tooltip"
            data-title="Transations / sec (last hour)"
            data-container="body"
            data-placement="bottom"
          >
          </sparkline>
        </div>
        <div class="col-md-6 mt-2 small text-center">
          <span class="text-muted" v-if="load1_last"> Loadavg: </span>
          <span class="badge badge-secondary" v-if="load1_last">
            {{ load1_last }}
          </span>
          <div ref="chart" data-toggle="tooltip" data-title="Load average (last hour)" data-placement="bottom"></div>
          <sparkline
            :data="load1_data"
            :start="start"
            :end="end"
            :colors="['#FAA43A']"
            @chart-rendered="setLastLoad1"
            ref="load1_chart"
            class="sparkline-container"
            data-toggle="tooltip"
            data-title="Load average (last hour)"
            data-placement="bottom"
          >
          </sparkline>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sparkline-container {
  height: 30px;
}
</style>
