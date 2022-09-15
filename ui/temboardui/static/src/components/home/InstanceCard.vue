<script type="text/javascript">
  import _ from 'lodash'
  import Dygraph from 'dygraphs'
  import 'dygraphs/dist/dygraph.css'
  import moment from 'moment'

  import Checks from './Checks.vue'
  import Sparkline from './Sparkline.vue'

  export default {
    data: function() { return {
      _chart: null,
      start: moment().subtract(1, 'hours'),
      end: moment(),
      tps_data: null,
      tps_last: 'N/A',
      load1_data: null,
      load1_last: 'N/A',
    } },
    computed: {
      dashboard_url: function() {
        return ['/server', this.instance.agent_address, this.instance.agent_port, 'dashboard'].join('/')
      },
      hasMonitoring: function() {
        return this.instance.plugins.indexOf('monitoring') != -1;
      }
    },
    props: ["instance", "index", "status_value"],
    components: {
      checks: Checks,
      sparkline: Sparkline
    },
    mounted: function() {
      if (this.index >= 18) {
        return
      }
      this.fetchChartData('tps')
      this.fetchChartData('load1')
    },
    watch: {
      instance: function() {
        if (this.index >= 18) {
          return
        }
        // Global start and end for each charts.
        this.start = moment().subtract(1, 'hours')
        this.end = moment()
        this.fetchChartData('tps')
        this.fetchChartData('load1')
      }
    },
    methods: {
      setLastPoint: function(metric, chart) {
        // Use Dygraphs to parse CSV and report last point in VueJS context.
        var last = chart.getValue(chart.numRows() - 1, 1);
        switch(metric) {
          case 'tps':
            this.tps_last = last || 'N/A'
            break
          case 'load1':
            this.load1_last = last || 'N/A'
            break
        }
      },
      fetchChartData: function(metric) {
        var url = ['/server', this.instance.agent_address, this.instance.agent_port, 'monitoring/data', metric].join('/');
        var params = "?start=" + this.start.toISOString() + "&end=" + this.end.toISOString();
        $.get(url + params).done(data => {
          if (!data) {
            return
          }
          switch(metric) {
            case 'tps':
              this.tps_data = data
              break
            case 'load1':
              this.load1_data = data
              break
          }
        })
      }
    }
  }
</script>

<template>
  <div :class="['card', {'border-danger bg-danger-light': status_value >= 1000000, 'border-warning bg-warning-light': status_value >= 1000}]">
    <div class="card-body p-2"
          style="min-height: 150px;">
      <div class="row">
        <div class="col-md-12">
          <p class="mb-0 overflow-ellipsis">
            <strong>
              <i class="fa fa-database"></i>
              <a :href="dashboard_url"
                  :title="instance.pg_version_summary + ' listening on ' + [instance.hostname, instance.pg_port].join(':')"
                  class="instance-link"
                  data-toggle="tooltip">
                  {{instance.hostname}}:{{instance.pg_port}}
              </a>
            </strong>
          </p>
          <p class="mb-0 small">
            <template v-for="(group, index) in instance.groups">
              <span class="badge border text-muted mr-1" :title="'Instance in group ' + group">
                {{group}}
              </span>
            </template>
            <span class="pg_version">{{instance.pg_version_summary || 'Unknown version'}}</span>
          </p>
          <checks :instance="instance"></checks>
        </div>
      </div>
      <!-- Limit graph to top 3 rows. -->
      <div class="row" v-if="hasMonitoring && index < 18">
        <div class="col-md-6 mt-2 small text-center">
          <span class="text-muted">
            TPS:
          </span>
          <span class="badge badge-secondary">
            {{ tps_last }}
          </span>
          <sparkline
            :instance="instance"
            :metric="'tps'"
            :data="tps_data"
            :start="start"
            :end="end"
            :colors="['#50BD68', '#F15854']"
            @chart-created="setLastPoint"
            @chart-updated="setLastPoint"
            ref="tps_chart"
            class="sparkline-container"
            data-toggle="tooltip"
            data-title="Transations / sec (last hour)"
            data-container="body"
            data-placement="bottom">
          </sparkline>
        </div>
        <div class="col-md-6 mt-2 small text-center">
          <span class="text-muted">
            Loadavg:
          </span>
          <span class="badge badge-secondary">
            {{ load1_last }}
          </span>
          <div
            ref="chart"
            data-toggle="tooltip"
            data-title="Load average (last hour)"
            data-placement="bottom">
          </div>
          <sparkline
            :instance="instance"
            :metric="'load1'"
            :data="load1_data"
            :start="start"
            :end="end"
            :colors="['#FAA43A']"
            @chart-created="setLastPoint"
            @chart-updated="setLastPoint"
            ref="load1_chart"
            class="sparkline-container"
            data-toggle="tooltip"
            data-title="Load average (last hour)"
            data-placement="bottom">
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
