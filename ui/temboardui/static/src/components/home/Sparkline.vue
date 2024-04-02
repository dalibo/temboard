<script setup>
import Dygraph from "dygraphs";
import _ from "lodash";
import moment from "moment";
import { ref, watch } from "vue";

const root = ref(null);
const chart = ref(null);
const props = defineProps(["data", "start", "end", "colors"]);

watch(
  () => props.data,
  () => {
    if (chart.value) {
      if (props.data) {
        chart.value.updateOptions({
          dateWindow: [props.start, props.end],
          file: props.data,
        });
      } else {
        chart.value.destroy();
        chart.value = null;
      }
    } else if (props.data) {
      chart.value = renderChart();
    }

    let last_value = null;
    if (chart.value) {
      last_value = chart.value.getValue(chart.value.numRows() - 1, 1);
    }
    emit("chart-rendered", last_value);
  },
);

function renderChart() {
  const chartOptions = {
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
    dateWindow: [props.start, props.end],
    legend: "never",
    xValueParser: function (x) {
      return moment(x).toDate().getTime();
    },
    highlightCircleSize: 0,
    interactionModel: {},
    colors: props.colors,
  };

  return new Dygraph(root.value, props.data, chartOptions);
}

const emit = defineEmits(["chart-rendered"]);
</script>

<template>
  <div ref="root">
    <div style="height: 100%; line-height: 30px" class="text-secondary align-bottom">No data</div>
  </div>
</template>
