/* global apiUrl, checkName, Vue, VueRouter, Dygraph, moment, dateMath */
$(function() {

  var v = new Vue({
    el: '#check-container',
    router: new VueRouter(),
    data: {
      keys: [],
      from: null,
      to: null
    },
    computed: {
      fromTo: function() {
        return '' + this.from + this.to;
      },
      sortedKeys: function() {
        return this.keys.sort(function(a, b) {
          return a.key > b.key;
        });
      }
    }
  });

  Vue.component('monitoring-chart', {
    props: [
      'check',
      'key_',
      'valueType',
      'foo',
      'from',
      'to'
    ],
    mounted: createOrUpdateChart,
    data: function() {
      return {
        chart: null
      };
    },
    watch: {
      // only one watcher for from + to
      fromTo: createOrUpdateChart
    },
    computed: {
      fromTo: function() {
        return '' + this.from + this.to;
      }
    },
    template: '<div class="monitoring-chart"></div>'
  });

  function createOrUpdateChart() {
    var startDate = v.from;
    var endDate = v.to;

    var defaultOptions = {
      axisLabelFontSize: 10,
      yLabelWidth: 14,
      ylabel: this.valueType == 'percent' ? '%' : '',
      includeZero: true,
      legend: 'always',
      labelsDiv: "legend" + this.key_,
      gridLineColor: 'rgba(128, 128, 128, 0.3)',
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
            var dates = g.dateWindow_;
            // synchronize charts on pan end
            onChartZoom(dates[0], dates[1]);
          } else if (context.isZooming) {
            Dygraph.endZoom(event, g, context);
            // don't do the same since zoom is animated
            // zoomCallback will do the job
          }
        }
      }
    };

    switch (this.valueType) {
    case 'percent':
      defaultOptions.valueRange = [0, 105];
      break;
    case 'memory':
      defaultOptions.labelsKMG2 = true;
      break;
    }

    var url = apiUrl + "/../monitoring/data/" + this.check + "?";
    url += $.param({
      key: this.key_,
      start: timestampToIsoDate(startDate),
      end: timestampToIsoDate(endDate)
    });

    var chart = this.chart;
    if (!this.chart) {
      chart = new Dygraph(
        document.getElementById("chart" + this.key_),
        url,
        defaultOptions
      );
    } else {
      chart.updateOptions({
        dateWindow: [startDate, endDate],
        file: url
      });
    }

    var self = this;
    chart.ready(function() {
      // Wait for both state changes and check changes to load
      // before drawing alerts and thresholds
      $.when(loadStateChanges(self.check, self.key_, startDate, endDate),
             loadCheckChanges(self.check, startDate, endDate))
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
    $('[data-toggle="tooltip"]').tooltip();
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
      var text = [
        '<span class="badge badge-',
        alert.state.toLowerCase(),
        '">',
        alert.state,
        '</span><br>'
      ];
      if (alert.state == 'WARNING' || alert.state == 'CRITICAL') {
        text = text.concat([
          alert.value,
          ' > ',
          alert[alert.state.toLowerCase()],
          '<br>'
        ]);
      }
      text.push(alert.datetime);
      return {
        series: chart.getLabels()[1],
        x: x,
        shortText: '♥',
        cssClass: 'alert-' + alert.state.toLowerCase(),
        text: text.join(''),
        tickColor: bgColors[alert.state.toLowerCase()],
        attachAtBottom: true
      };
    });
    chart.setAnnotations(annotations);
    window.setTimeout(function() {
      $('.dygraph-annotation').each(function() {
        $(this).attr('data-content', $(this).attr('title'));
        $(this).attr('title', '');
      });
      $('.dygraph-annotation').popover({
        trigger: 'hover',
        placement: 'top',
        html: true
      });
    }, 1);
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
   *  - from: the start date
   *  - to: the end date
   */
  function loadCheckChanges(check, from, to) {
    var url = apiUrl + "/check_changes/" + check + ".json";
    var params = {
      start: timestampToIsoDate(from),
      end: timestampToIsoDate(to),
      noerror: 1
    };
    url += '?' + $.param(params);
    return $.ajax({url: url});
  }

  var colors = {
    'ok': 'green',
    'warning': 'orange',
    'critical': 'red',
    'undef': '#ccc'
  };

  var bgColors = {
    'ok': 'green',
    'warning': 'rgba(255, 120, 0, .2)',
    'critical': 'rgba(255, 0, 0, .2)',
    'undef': 'rgba(192, 192, 192, .2)'
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
    var url = apiUrl + "/state_changes/" + check + ".json";
    var params = {
      key: key,
      start: timestampToIsoDate(from),
      end: timestampToIsoDate(to),
      noerror: 1
    };
    url += '?' + $.param(params);
    return $.ajax({url: url});
  }

  // Find the corresponding x in already existing data
  // If not available, return the closest x
  function getClosestX(g, x) {
    // x already exist in chart
    if (g.getRowForX(x)) {
      return x;
    }
    // find the closest
    var rows = g.numRows();
    var gDiff = Infinity;
    var goal = new Date(x).getTime();
    var closest = x;
    var curr;
    var i = 0;
    var l = rows - 1;
    for (i; i < l; i++) {
      curr = g.getValue(i, 0);
      diff = Math.abs(curr - goal);
      if (gDiff > diff) {
        gDiff = diff;
        closest = curr;
      }
    }
    return closest;
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
      $('#submitFormUpdateCheck').attr('disabled', true);
      $('#modalInfo').html('<div class="alert alert-success" role="alert">SUCESS: Will be taken into account shortly (next check)</div>');
      hideWaiter();
      window.setTimeout(function() {
        window.location.reload();
      }, 3000);
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

  function getHashParams() {

    var hashParams = {};
    var e;
    var a = /\+/g;  // Regex for replacing addition symbol with a space
    var r = /([^&;=]+)=?([^&;]*)/g;
    var d = function (s) {
      return decodeURIComponent(s.replace(a, " "));
    };
    var q = window.location.hash.substring(1);

    while (e = r.exec(q)) {
      hashParams[d(e[1])] = d(e[2]);
    }

    return hashParams;
  }

  function onChartZoom(min, max) {
    v.$refs.daterangepicker.setFromTo(moment(min), moment(max));
  }

  // remove any previous popover on annotation
  $('.dygraph-annotation').popover('dispose');
  $.ajax({
    url: apiUrl + "/states/" + checkName + ".json"
  }).success(function(data) {
    v.keys = data;
  }).error(function(error) {
    console.error(error);
  });
});
