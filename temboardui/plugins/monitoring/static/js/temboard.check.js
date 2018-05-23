/* global apiUrl, checkName, Vue, Dygraph, moment */
$(function() {

  var v = new Vue({
    el: '#check-container',
    data: {
      keys: null
    },
    watch: {}
  });

  var startDate = moment().subtract(2, 'hour');
  var endDate = moment();

  function refresh() {
    $.ajax({
      url: apiUrl + "/states/" + checkName + ".json"
    }).success(function(data) {
      v.keys = data;
    }).error(function(error) {
      console.error(error);
    });
  }

  // refresh every 1 min
  window.setInterval(function() {
    refresh();
  }, 60 * 1000);
  refresh();

  Vue.component('monitoring-chart', {
    props: ['check', 'key_'],
    mounted: function() {
      newGraph(this.check, this.key_);
    },
    template: '<div class="monitoring-chart"></div>'
  });

  function newGraph(check, key) {

    var defaultOptions = {
      axisLabelFontSize: 10,
      yLabelWidth: 14,
      dateWindow: [
        new Date(startDate).getTime(),
        new Date(endDate).getTime()
      ],
      xValueParser: function(x) {
        var m = moment(x);
        return m.toDate().getTime();
      },
      // since we show only one key at a time we actually
      // want the series to be stacked
      stackedGraph: true
    };

    var chart = new Dygraph(
      document.getElementById("chart" + key),
      apiUrl+"/../monitoring/data/"+ check + "?key=" + key + "&start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate),
      defaultOptions
    );

    chart.ready(function() {
      // Wait for both state changes and check changes to load
      // before drawing alerts and thresholds
      $.when(loadStateChanges(check, key),
             loadCheckChanges(check))
        .done(function(states, checks) {
          var statesData = states[0].reverse();
          drawAlerts(chart, statesData);

          var checksData = checks[0].reverse();

          chart.updateOptions({
            underlayCallback: function(canvas, area) {
              drawThreshold(chart, checksData, canvas);
              drawAlertsBg(chart, statesData, canvas, area);
            }
          });
        })
        .fail(function() {
          console.error("Something went wrong");
        });
    });
  }

  function drawThreshold(chart, data, canvas) {
    data.forEach(function(alert, index) {
      if (index == data.length - 1) {
        return;
      }

      ['warning', 'critical'].forEach(function(level) {
        var y = alert[level];
        var left = chart.toDomCoords(new Date(alert.datetime), y);
        var right = chart.toDomCoords(new Date(data[index + 1].datetime), y);
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

  function drawAlerts(chart, data) {
    var annotations = data.map(function(alert) {
      var x = getClosestX(chart, alert.datetime);
      return {
        series: chart.getLabels()[1],
        x: x,
        shortText: '♥',
        cssClass: 'alert-' + alert.state.toLowerCase(),
        text: alert.state,
        tickColor: bgColors[alert.state.toLowerCase()],
        attachAtBottom: true
      };
    });
    chart.setAnnotations(annotations);
  }

  function drawAlertsBg(chart, data, canvas, area) {
    data.forEach(function(alert, index) {
      if (alert.state == 'OK') {
        return;
      }

      var bottom_left = chart.toDomCoords(new Date(alert.datetime), 0);
      // Right boundary is next alert or end of visible series
      var right;
      if (index == data.length - 1) {
        var rows = chart.numRows();
        right = chart.getValue(rows - 1, 0);
      } else {
        right = new Date(data[index + 1].datetime);
      }
      var top_right = chart.toDomCoords(right, 10);
      var left = bottom_left[0];
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
   */
  function loadCheckChanges(check) {
    var url = apiUrl + "/check_changes/" + check + ".json";
    var params = {
      start: timestampToIsoDate(startDate),
      end: timestampToIsoDate(endDate),
      noerror: 1
    };
    url += '?' + $.param(params);
    return $.ajax({url: url});
  }

  var colors = {
    'ok': 'green',
    'warning': 'orange',
    'critical': 'red'
  };

  var bgColors = {
    'ok': 'green',
    'warning': 'rgba(255, 120, 0, .2)',
    'critical': 'rgba(255, 0, 0, .2)'
  };

  /**
   * Load and display alerts in chart
   * `this` correspond to the chart
   *
   * Arguments:
   *  - check: the monitoring check (ex: cpu_core)
   *  - key : the check key (ex: cpu1)
   */
  function loadStateChanges(check, key) {
    var url = apiUrl + "/state_changes/" + check + ".json";
    var params = {
      key: key,
      start: timestampToIsoDate(startDate),
      end: timestampToIsoDate(endDate),
      noerror: 1
    };
    url += '?' + $.param(params);
    return $.ajax({url: url});
  }

  // Find the corresponding x in already existing data
  // If not available, return the closest (left hand) x
  function getClosestX(g, x) {
    // x already exist in chart
    if (g.getRowForX(x)) {
      return x;
    }
    // find the closest (left hand)
    var rows = g.numRows();
    for (var i = 0, l = rows - 1; i < l; i++) {
      if (g.getValue(i, 0) > new Date(x).getTime()) {
        return g.getValue(i - 1, 0);
      }
    }
    return x;
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }

  $('#submitFormUpdateCheck').click(function() {
    $('#updateForm').submit();
  });

  $('#updateForm').submit(function(event) {
    event.preventDefault();
    updateCheck();
  });

  function updateCheck() {
    $.ajax({
      url: apiUrl + "/checks.json",
      method: 'post',
      dataType: "json",
      beforeSend: showWaiter,
      data: JSON.stringify({
        checks: [{
          name: checkName,
          description: $('#descriptionInput').val(),
          warning: parseFloat($('#warningThresholdInput').val()),
          critical: parseFloat($('#criticalThresholdInput').val()),
          enabled: $('#enabledInput').is(':checked')
        }]
      })
    }).success(function() {
      $('#modalInfo').html('');
      hideWaiter();
      window.location.reload();
    }).error(function(xhr) {
      hideWaiter();
      $('#modalInfo').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
    });
  }

  var entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': '&quot;',
    "'": '&#39;',
    "/": '&#x2F;'
  };

  function escapeHtml(string) {
    return String(string).replace(/[&<>"'\/]/g, function (s) {
      return entityMap[s];
    });
  }

  function showWaiter() {
    $('#updateModal .loader').removeClass('d-none');
  }

  function hideWaiter() {
    $('#updateModal .loader').addClass('d-none');
  }
});
