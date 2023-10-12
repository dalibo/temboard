<script type="text/javascript">
import _ from "lodash";
import Dygraph from "dygraphs";
import moment from "moment";

export default {
  data: function () {
    return {
      chart: null,
    };
  },
  props: ["data", "start", "end", "colors"],
  watch: {
    data: function () {
      if (this.chart) {
        if (this.data) {
          this.chart.updateOptions({
            dateWindow: [this.start, this.end],
            file: this.data,
          });
        } else {
          this.chart.destroy();
          this.chart = null;
        }
      } else if (this.data) {
        this.chart = this.renderChart();
      }

      var last_value = null;
      if (this.chart) {
        last_value = this.chart.getValue(this.chart.numRows() - 1, 1);
      }
      this.$emit("chart-rendered", last_value);
    },
  },
  methods: {
    renderChart: function () {
      var chartOptions = {
        axes: {
          x: {
            drawAxis: false,
            drawGrid: false,
          },
          y: {
            drawAxis: false,
            drawGrid: false,
          },
        },
        dateWindow: [this.start, this.end],
        legend: "never",
        xValueParser: function (x) {
          return moment(x).toDate().getTime();
        }.bind(this),
        highlightCircleSize: 0,
        interactionModel: {},
        colors: this.colors,
      };

      return new Dygraph(this.$el, this.data, chartOptions);
    },
  },
};
</script>

<template>
  <div>
    <div style="height: 100%; line-height: 30px" class="text-secondary align-bottom" v-if="!data">No data</div>
  </div>
</template>
