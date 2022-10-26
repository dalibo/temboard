<script type="text/javascript">
  import _ from 'lodash'
  import Dygraph from 'dygraphs'
  import moment from 'moment'

  export default {
    data: function() {
      return {
        chartOptions: {},
        chart: null
      }
    },
    props: ['instance', 'metric', 'data', 'start', 'end', 'colors'],
    mounted: function() {
      if (this.data) {
        this.renderChart()
      }
    },
    watch: {
      data: function() {
        if (this.data) {
          this.renderChart()
        }
      }
    },
    methods: {
      renderChart: function() {
        this.chartOptions = {
          axes: {
            x: {
              drawAxis: false,
              drawGrid: false
            },
            y: {
              drawAxis: false,
              drawGrid: false
            }
          },
          dateWindow: [this.start, this.end],
          legend: 'never',
          xValueParser: function(x) {
            return moment(x).toDate().getTime();
          }.bind(this),
          highlightCircleSize: 0,
          interactionModel: {},
          colors: this.colors
        }

        this.chart = new Dygraph(this.$el, this.data, this.chartOptions)
        this.$emit('chart-created', this.metric, this.chart)
      }
    }
  }
</script>

<template>
  <div>
    <div style="height: 100%; line-height: 30px;" class="text-secondary align-bottom" v-if="!data">No data</div>
  </div>
</template>
