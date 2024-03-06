<script setup>
import { inject, onMounted, ref, watch } from "vue";

const props = defineProps(["graph", "metrics", "from", "to"]);
const chartEl = ref(null);

let chart;

const setFromTo = inject("setFromTo");

watch(() => "" + props.from + props.to, createOrUpdateChart);

onMounted(createOrUpdateChart);

function createOrUpdateChart(create) {
  const id = props.graph;
  const startDate = props.from;
  const endDate = props.to;

  const defaultOptions = {
    axisLabelFontSize: 10,
    yLabelWidth: 14,
    legend: "always",
    labelsDiv: "legend" + id,
    labelsKMB: true,
    animatedZooms: true,
    gridLineColor: "#DDDDDD",
    dateWindow: [new Date(startDate).getTime(), new Date(endDate).getTime()],
    xValueParser: function (x) {
      const m = moment(x);
      return m.toDate().getTime();
    },
    drawCallback: function (g, isInitial) {
      addVisibilityCb(id, g, isInitial);
      if (g.numRows() === 0) {
        $("#nodata" + id).removeClass("d-none");
      } else {
        $("#nodata" + id).addClass("d-none");
      }
    },
    zoomCallback: onChartZoom,
    // change interaction model in order to be able to capture the end of
    // panning
    // Dygraphs doesn't provide any panCallback unfortunately
    interactionModel: {
      mousedown: function (event, g, context) {
        context.initializeMouseDown(event, g, context);
        if (event.shiftKey) {
          Dygraph.startPan(event, g, context);
        } else {
          Dygraph.startZoom(event, g, context);
        }
      },
      mousemove: function (event, g, context) {
        if (context.isPanning) {
          Dygraph.movePan(event, g, context);
        } else if (context.isZooming) {
          Dygraph.moveZoom(event, g, context);
        }
      },
      mouseup: function (event, g, context) {
        if (context.isPanning) {
          Dygraph.endPan(event, g, context);
          const dates = g.dateWindow_;
          // synchronize charts on pan end
          onChartZoom(dates[0], dates[1]);
        } else if (context.isZooming) {
          Dygraph.endZoom(event, g, context);
          // don't do the same since zoom is animated
          // zoomCallback will do the job
        }
      },
    },
  };

  for (var attrname in props.metrics[id].options) {
    defaultOptions[attrname] = props.metrics[id].options[attrname];
  }

  const params = "?start=" + timestampToIsoDate(startDate) + "&end=" + timestampToIsoDate(endDate) + "&noerror=1";
  let data = null;
  const dataReq = $.get(apiUrl + "/" + props.metrics[id].api + params, function (_data) {
    data = _data;
  });
  // Get the dates when the instance was unavailable
  let unavailabilityData = "";
  let promise = $.when(dataReq);
  if (props.metrics[id].category == "postgres") {
    promise = $.when(
      dataReq,
      $.get(unavailabilityUrl + params, function (_data) {
        unavailabilityData = _data;
      }),
    );
  }
  promise.then(function () {
    // fill unavailability data with NaN
    const colsCount = data.split("\n")[0].split(",").length;
    const nanArray = new Array(colsCount - 1).fill("NaN");
    nanArray.unshift("");
    unavailabilityData = unavailabilityData.replace(/\n/g, nanArray.join(",") + "\n");

    // do the job when all ajax request have succeeded
    if (!chart || create) {
      chart = new Dygraph(chartEl.value, data + unavailabilityData, defaultOptions);
    } else {
      chart.ready(function () {
        // update the date range
        chart.updateOptions({
          dateWindow: [startDate, endDate],
        });

        // load the data for the given range
        chart.updateOptions(
          {
            file: data + unavailabilityData,
          },
          false,
        );
      });
    }
  });
}

function timestampToIsoDate(epochMs) {
  const ndate = new Date(epochMs);
  return ndate.toISOString();
}

function addVisibilityCb(chartId, g, isInitial) {
  if (!isInitial) return;

  let nbLegendItem = 0;
  let visibilityHtml = "";
  let cbIds = [];
  $("#legend" + chartId)
    .children("span")
    .each(function () {
      visibilityHtml += '<input type="checkbox" id="' + chartId + "CB" + nbLegendItem + '" checked>';
      visibilityHtml +=
        '<label for="' +
        chartId +
        "CB" +
        nbLegendItem +
        '" style="' +
        $(this).attr("style") +
        '"> ' +
        $(this).text() +
        "</label>  ";
      cbIds.push(chartId + "CB" + nbLegendItem);
      nbLegendItem++;
    });
  $("#visibility" + chartId).html(visibilityHtml);
  cbIds.forEach(function (id) {
    $("#" + id).change(function () {
      g.setVisibility(
        parseInt(
          $(this)
            .attr("id")
            .replace(chartId + "CB", ""),
        ),
        $(this).is(":checked"),
      );
    });
  });
}

function onChartZoom(min, max) {
  setFromTo(moment(min), moment(max));
}
</script>
<template>
  <div class="monitoring-chart" ref="chartEl"></div>
</template>
