<script setup>
import $ from "jquery";
import moment from "moment";
import { inject, onMounted, ref, watch } from "vue";

const props = defineProps(["check", "key_", "valueType", "from", "to"]);
const chartEl = ref(null);

let chart;

const setFromTo = inject("setFromTo");

watch(() => "" + props.from + props.to, createOrUpdateChart);

onMounted(createOrUpdateChart);

function createOrUpdateChart() {
  const startDate = props.from;
  const endDate = props.to;

  const defaultOptions = {
    axisLabelFontSize: 10,
    yLabelWidth: 14,
    ylabel: props.valueType == "percent" ? "%" : "",
    includeZero: true,
    legend: "always",
    labelsDiv: "legend" + props.key_,
    gridLineColor: "rgba(128, 128, 128, 0.3)",
    dateWindow: [new Date(startDate).getTime(), new Date(endDate).getTime()],
    xValueParser: function (x) {
      const m = moment(x);
      return m.toDate().getTime();
    },
    // since we show only one key at a time we actually
    // want the series to be stacked
    stackedGraph: true,
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

  switch (props.valueType) {
    case "percent":
      defaultOptions.valueRange = [0, 105];
      break;
    case "memory":
      defaultOptions.labelsKMG2 = true;
      break;
  }

  let url = apiUrl + "/../monitoring/data/" + props.check + "?";
  url += $.param({
    key: props.key_,
    start: timestampToIsoDate(startDate),
    end: timestampToIsoDate(endDate),
  });

  if (!chart) {
    chart = new Dygraph(chartEl.value, url, defaultOptions);
  } else {
    chart.updateOptions({
      dateWindow: [startDate, endDate],
      file: url,
    });
  }

  chart.ready(function () {
    // Wait for both state changes and check changes to load
    // before drawing alerts and thresholds
    $.when(
      loadStateChanges(props.check, props.key_, startDate, endDate),
      loadCheckChanges(props.check, startDate, endDate),
    )
      .done(function (states, checks) {
        const statesData = states[0].reverse();
        drawAlerts(statesData);

        const checksData = checks[0].reverse();

        chart.updateOptions({
          underlayCallback: function (canvas, area) {
            drawThreshold(checksData, canvas);
            drawAlertsBg(statesData, canvas, area);
          },
        });
      })
      .fail(function () {
        console.error("Something went wrong");
      });
  });
  $('[data-bs-toggle="tooltip"]').tooltip();
}

function drawThreshold(data, canvas) {
  data.forEach(function (alert, index) {
    if (index == data.length - 1) {
      return;
    }

    ["warning", "critical"].forEach(function (level) {
      const y = alert[level];
      const left = chart.toDomCoords(new Date(alert.datetime), y);
      const right = chart.toDomCoords(new Date(data[index + 1].datetime), y);
      canvas.beginPath();
      canvas.strokeStyle = colors[level];
      if (!alert.enabled) {
        canvas.setLineDash([5, 5]);
      }
      canvas.moveTo(left[0], left[1]);
      canvas.lineTo(right[0], right[1]);
      canvas.stroke();
      canvas.setLineDash([]);
      canvas.closePath();
    });
  });
}

function drawAlerts(data) {
  const annotations = data.map(function (alert) {
    const x = getClosestX(alert.datetime);
    let text = ['<span class="badge text-bg-', alert.state.toLowerCase(), '">', alert.state, "</span><br>"];
    if (alert.state == "WARNING" || alert.state == "CRITICAL") {
      text = text.concat([alert.value, " > ", alert[alert.state.toLowerCase()], "<br>"]);
    }
    text.push(alert.datetime);
    return {
      series: chart.getLabels()[1],
      x: x,
      shortText: "♥",
      cssClass: "alert-" + alert.state.toLowerCase(),
      text: text.join(""),
      tickColor: bgColors[alert.state.toLowerCase()],
      attachAtBottom: true,
    };
  });
  chart.setAnnotations(annotations);
  window.setTimeout(function () {
    $(".dygraph-annotation").each(function () {
      $(this).attr("data-bs-content", $(this).attr("title"));
      $(this).attr("title", "");
    });
    $(".dygraph-annotation").popover({
      trigger: "hover",
      placement: "top",
      html: true,
    });
  }, 1);
}

function drawAlertsBg(data, canvas, area) {
  data.forEach(function (alert, index) {
    if (alert.state == "OK") {
      return;
    }

    const bottom_left = chart.toDomCoords(new Date(alert.datetime), 0);
    // Right boundary is next alert or end of visible series
    let right;
    if (index == data.length - 1) {
      const rows = chart.numRows();
      right = chart.getValue(rows - 1, 0);
    } else {
      right = new Date(data[index + 1].datetime);
    }
    const top_right = chart.toDomCoords(right, 10);
    let left = bottom_left[0];
    right = top_right[0];

    canvas.fillStyle = bgColors[alert.state.toLowerCase()];
    canvas.fillRect(left, area.y, right - left, area.h);
  });
}

/**
 * Load check changes
 * `this` correspond to the chart
 *
 * Arguments:
 *  - check: the monitoring check (ex: cpu_core)
 *  - from: the start date
 *  - to: the end date
 */
function loadCheckChanges(check, from, to) {
  let url = apiUrl + "/check_changes/" + check + ".json";
  const params = {
    start: timestampToIsoDate(from),
    end: timestampToIsoDate(to),
    noerror: 1,
  };
  url += "?" + $.param(params);
  return $.ajax({ url: url });
}

const colors = {
  ok: "green",
  warning: "orange",
  critical: "red",
  undef: "#ccc",
};

const bgColors = {
  ok: "green",
  warning: "rgba(255, 120, 0, .2)",
  critical: "rgba(255, 0, 0, .2)",
  undef: "rgba(192, 192, 192, .2)",
};

/**
 * Load and display alerts in chart
 * `this` correspond to the chart
 *
 * Arguments:
 *  - check: the monitoring check (ex: cpu_core)
 *  - key : the check key (ex: cpu1)
 *  - from: the start date
 *  - to: the end date
 */
function loadStateChanges(check, key, from, to) {
  let url = apiUrl + "/state_changes/" + check + ".json";
  const params = {
    key: key,
    start: timestampToIsoDate(from),
    end: timestampToIsoDate(to),
    noerror: 1,
  };
  url += "?" + $.param(params);
  return $.ajax({ url: url });
}

// Find the corresponding x in already existing data
// If not available, return the closest x
function getClosestX(x) {
  // x already exist in chart
  if (chart.getRowForX(x)) {
    return x;
  }
  // find the closest
  const rows = chart.numRows();
  let gDiff = Infinity;
  const goal = new Date(x).getTime();
  let closest = x;
  let curr;
  let i = 0;
  const l = rows - 1;
  let diff;
  for (i; i < l; i++) {
    curr = chart.getValue(i, 0);
    diff = Math.abs(curr - goal);
    if (gDiff > diff) {
      gDiff = diff;
      closest = curr;
    }
  }
  return closest;
}

function timestampToIsoDate(epochMs) {
  const ndate = new Date(epochMs);
  return ndate.toISOString();
}

$("#submitFormUpdateCheck").click(function () {
  $("#updateForm").submit();
});

$("#updateForm").submit(function (event) {
  event.preventDefault();
  updateCheck();
});

function updateCheck() {
  $.ajax({
    url: apiUrl + "/checks.json",
    method: "post",
    dataType: "json",
    beforeSend: showWaiter,
    data: JSON.stringify({
      checks: [
        {
          name: props.check,
          description: $("#descriptionInput").val(),
          warning: parseFloat($("#warningThresholdInput").val()),
          critical: parseFloat($("#criticalThresholdInput").val()),
          enabled: $("#enabledInput").is(":checked"),
        },
      ],
    }),
  })
    .success(function () {
      $("#submitFormUpdateCheck").attr("disabled", true);
      $("#modalInfo").html(
        '<div class="alert alert-success" role="alert">SUCCESS: Will be taken into account shortly (next check)</div>',
      );
      hideWaiter();
      window.setTimeout(function () {
        window.location.reload();
      }, 3000);
    })
    .error(function (xhr) {
      hideWaiter();
      $("#modalInfo").html(
        '<div class="alert alert-danger" role="alert">ERROR: ' +
          escapeHtml(JSON.parse(xhr.responseText).error) +
          "</div>",
      );
    });
}

const entityMap = {
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

function showWaiter() {
  $("#updateModal .loader").removeClass("d-none");
}

function hideWaiter() {
  $("#updateModal .loader").addClass("d-none");
}

function onChartZoom(min, max) {
  setFromTo(moment(min), moment(max));
}
</script>

<template>
  <div class="monitoring-chart" ref="chartEl"></div>
</template>
