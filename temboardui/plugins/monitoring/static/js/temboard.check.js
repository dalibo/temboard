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
      connectSeparatedPoints: true,
      series: {
        warning: {
          stepPlot: true
        },
        critical: {
          stepPlot: true
        }
      }
      // since we show only one key at a time we actually
      // want the series to be stacked
      //stackedGraph: true
    };

    var chart = new Dygraph(
      document.getElementById("chart" + key),
      apiUrl+"/../monitoring/data/"+ check + "?key=" + key + "&start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate),
      defaultOptions
    );
    chart.ready(function(chart) {
      loadAlerts.call(chart, check, key);
      loadThresholds.call(chart, check);
    });
  }

  /**
   * Load threshold changes
   * `this` correspond to the chart
   *
   * Arguments:
   *  - check: the monitoring check (ex: cpu_core)
   */
  function loadThresholds(check) {
    var chart = this;
    var labels = chart.getLabels();
    // number of series (we also exclude date)
    var seriesCount = labels.length - 1;
    var newData = chart.rawData_;
    newData.forEach(function(item, index) {
      item[0] = new Date(item[0]);
      item = item.concat([null, null]);
      newData[index] = item;
    });

    $.ajax({
      url: apiUrl+"/check_changes/" + check + ".json?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1"
    }).success(function(data) {
      data.forEach(function(item) {
        var datum = [new Date(item.datetime)];
        // add null values in place of series
        datum = datum.concat(initArray(seriesCount, null));
        // then add the threshold data
        datum = datum.concat([item.warning, item.critical]);
        newData.push(datum);
      });

      // sort
      newData.sort(function(a, b) {
        return a[0] - b[0];
      });

      labels = labels.concat(['warning', 'critical']);
      chart.updateOptions({
        file: newData,
        labels: labels,
        colors: chart.getColors().concat(['orange', 'red'])
      });
    }).error(function(error) {
      console.log (error);
    });
  }

  /**
   * Load and display alerts in chart
   * `this` correspond to the chart
   *
   * Arguments:
   *  - check: the monitoring check (ex: cpu_core)
   *  - key : the check key (ex: cpu1)
   */
  function loadAlerts(check, key) {
    var chart = this;
    var colors = {
      'OK': 'green',
      'WARNING': 'rgba(255, 120, 0, .2)',
      'CRITICAL': 'rgba(255, 0, 0, .2)'
    };
    $.ajax({
      url: apiUrl+"/state_changes/" + check + ".json?key=" + key + "&start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1",
    }).success(function(data) {
      data = data.reverse();
      chart.setAnnotations(data.map(function(alert) {
        var x = getClosestX(chart, alert.datetime);
        return {
          series: chart.getLabels()[1],
          x: x,
          shortText: '♥',
          cssClass: 'alert-' + alert.state.toLowerCase(),
          text: alert.state,
          tickColor: colors[alert.state],
          attachAtBottom: true
        };
      }));

      chart.updateOptions({
        underlayCallback: function(canvas, area, g) {
          data.forEach(function(alert, index) {
            if (alert.state == 'OK') {
              return;
            }

            var bottom_left = g.toDomCoords(new Date(alert.datetime), 0);
            // Right boundary is next alert or end of visible series
            var right;
            if (index == data.length - 1) {
              var rows = g.numRows();
              right = g.getValue(rows - 1, 0);
            } else {
              right = new Date(data[index + 1].datetime);
            }
            var top_right = g.toDomCoords(right, 10);
            var left = bottom_left[0];
            right = top_right[0];

            canvas.fillStyle = colors[alert.state];
            canvas.fillRect(left, area.y, right - left, area.h);
          });
        }
      });
    });
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

  function initArray(n, v) {
    var arr = Array.apply(null, Array(n));
    return arr.map(function() { return v; });
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
