$(function() {
  var colors = {
    blue: "#5DA5DA",
    blue2: "#226191",
    green: "#60BD68",
    red: "#F15854",
    gray: "#4D4D4D",
    light_gray: "#AAAAAA",
    orange: "#FAA43A"
  };
  var dateFormat = 'DD/MM/YYYY HH:mm';

  /**
   * Parse location hash to get start and end date
   * If dates are not provided, falls back to the date range corresponding to
   * the last 24 hours.
   */
  var start;
  var end;
  var now = moment();
  var minus24h = now.clone().subtract(24, 'hours');
  var p = getHashParams();
  var g;

  if (p.start && p.end) {
    start = moment(parseInt(p.start, 10));
    end = moment(parseInt(p.end, 10));
  }
  start = start && start.isValid() ? start : minus24h;
  end = end && end.isValid() ? end : now;

  $("#daterange").daterangepicker({
    startDate: start,
    endDate: end,
    alwaysShowCalendars: true,
    timePicker: true,
    timePickerIncrement: 5,
    timePicker24Hour: true,
    opens: 'left',
    locale: {
      format: dateFormat
    },
    ranges: {
      'Last Hour': [now.clone().subtract(1, 'hours'), now],
      'Last 24 Hours': [minus24h, now],
      'Last 7 Days': [now.clone().subtract(7, 'days'), now],
      'Last 30 Days': [now.clone().subtract(30, 'days'), now],
      'Last 12 Months': [now.clone().subtract(12, 'months'), now]
    }
  });
  updateDateRange(start, end);
  $('#daterange').on('apply.daterangepicker', function(ev, picker) {
    synchronizeZoom(
      picker.startDate,
      picker.endDate,
      true
    );
  });

  var metrics = {
    "Loadavg": {
      title: "Loadaverage",
      api: "loadavg",
      options: {
        colors: [colors.blue, colors.orange, colors.green],
        ylabel: "Loadaverage"
      },
      category: 'system',
      alertsApi: 'loadaverage'
    },
    "CPU": {
      title: "CPU Usage",
      api: "cpu",
      options: {
        colors: [colors.blue, colors.green, colors.red, colors.gray],
        ylabel: "%",
        stackedGraph: true
      },
      category: 'system',
      alertsApi: 'cpu'
    },
    "CtxForks": {
      title: "Context switches and forks per second",
      api: "ctxforks",
      options: {
        colors: [colors.blue, colors.green]
      },
      category: 'system'
    },
    "Memory": {
      title: "Memory usage",
      api: "memory",
      options: {
        colors: [colors.light_gray, colors.green, colors.blue, colors.orange],
        ylabel: "Memory",
        labelsKMB: false,
        labelsKMG2: true,
        stackedGraph: true
      },
      category: 'system',
      alertsApi: 'memory'
    },
    "Swap": {
      title: "Swap usage",
      api: "swap",
      options: {
        colors: [colors.red],
        ylabel: "Swap",
        labelsKMB: false,
        labelsKMG2: true,
        stackedGraph: true
      },
      category: 'system',
      alertsApi: 'swap'
    },
    "FsSize": {
      title: "Filesystems size",
      api: "fs_size",
      options: {
        ylabel: "Size",
        labelsKMB: false,
        labelsKMG2: true
      },
      category: 'system',
      alertsApi: 'fs'
    },
    "FsUsage": {
      title: "Filesystems usage",
      api: "fs_usage",
      options: {
        ylabel: "%"
      },
      category: 'system',
      alertsApi: 'fs'
    },
    // PostgreSQL
    "TPS": {
      title: "Transactions per second",
      api: "tps",
      options: {
        colors: [colors.green, colors.red],
        ylabel: "Transactions",
        stackedGraph: true
      },
      category: 'postgres'
    },
    "InstanceSize": {
      title: "Instance size",
      api: "instance_size",
      options: {
        colors: [colors.blue],
        ylabel: "Size",
        stackedGraph: true,
        labelsKMB: false,
        labelsKMG2: true
      },
      category: 'postgres'
    },
    "TblspcSize": {
      title: "Tablespaces size",
      api: "tblspc_size",
      options: {
        ylabel: "Size",
        stackedGraph: true,
        labelsKMB: false,
        labelsKMG2: true
      },
      category: 'postgres'
    },
    "Sessions": {
      title: "Sessions",
      api: "sessions",
      options: {
        ylabel: "Sessions",
        stackedGraph: true
      },
      category: 'postgres',
      alertsApi: 'sessions'
    },
    "Blocks": {
      title: "Blocks Hit vs Read per second",
      api: "blocks",
      options: {
        colors: [colors.red, colors.green],
        ylabel: "Blocks"
      },
      category: 'postgres',
      alerts: 'hitratio'
    },
    "HRR": {
      title: "Blocks Hit vs Read ratio",
      api: "hitreadratio",
      options: {
        colors: [colors.blue],
        ylabel: "%"
      },
      category: 'postgres',
      alerts: 'hitratio'
    },
    "Checkpoints": {
      title: "Checkpoints",
      api: "checkpoints",
      options: {
        ylabel: "Checkpoints",
        y2label: "Duration",
        series: {
          'write_time': {
            axis: 'y2'
          },
          'sync_time': {
            axis: 'y2'
          }
        }
      },
      category: 'postgres'
    },
    "WalFilesSize": {
      title: "WAL Files size",
      api: "wal_files_size",
      options: {
        colors: [colors.blue, colors.blue2],
        labelsKMB: false,
        labelsKMG2: true,
        ylabel: "Size"
      },
      category: 'postgres'
    },
    "WalFilesCount": {
      title: "WAL Files",
      api: "wal_files_count",
      options: {
        colors: [colors.blue, colors.blue2],
        ylabel: "WAL files"
      },
      category: 'postgres',
      alertsApi: 'wal_files'
    },
    "WalFilesRate": {
      title: "WAL Files written rate",
      api: "wal_files_rate",
      options: {
        colors: [colors.blue],
        ylabel: "Byte per second",
        labelsKMB: false,
        labelsKMG2: true,
        stackedGraph: true
      },
      category: 'postgres'
    },
    "WBuffers": {
      title: "Written buffers",
      api: "w_buffers",
      options: {
        ylabel: "Written buffers",
        stackedGraph: true
      },
      category: 'postgres'
    },
    "Locks": {
      title: "Locks",
      api: "locks",
      options: {
        ylabel: "Locks"
      },
      category: 'postgres'
    },
    "WLocks": {
      title: "Waiting Locks",
      api: "waiting_locks",
      options: {
        ylabel: "Waiting Locks"
      },
      category: 'postgres',
      alertsApi: 'waiting'
    }
  };

  Vue.component('monitoring-chart', {
    props: ['graph'],
    mounted: function() {
      newGraph(this.graph);
    },
    watch: {
      graph: function() {
        // recreate the chart if metric changes
        newGraph(this.graph);
      }
    },
    template: '<div class="monitoring-chart"></div>'
  });

  function isVisible(metric) {
    return this.graphs.map(function(graph) {return graph.id;}).indexOf(metric) != -1;
  }

  function setVisible(metric, event) {
    if (event.target.checked) {
      this.graphs.splice(0, 0, {
        id: metric,
        chart: null
      });
    } else {
      this.removeGraph(metric);
    }
  }

  function selectAll(event) {
    loadGraphs(Object.keys(metrics));
  }

  function unselectAll(event) {
    loadGraphs([]);
  }

  function removeGraph(graph) {
    var index = -1;
    this.graphs.forEach(function(item, index) {
      if (item.id == graph) {
        this.graphs.splice(index, 1);
      }
    }.bind(this));
  }

  function loadGraphs(list) {
    v.graphs = list.map(function(item) {
      return {
        id: item,
        chart: null
      };
    });
  }

  var v = new Vue({
    el: '#charts-container',
    data: {
      // each graph is an Object with id and chart properties
      graphs: [],
      metrics: metrics,
      themes: [{
        title: 'Performance',
        graphs: ['Loadavg', 'CPU', 'TPS', 'Sessions']
      }, {
        title: 'Locks',
        graphs: ['Locks', 'WLocks', 'Sessions']
      }, {
        title: 'Size',
        graphs: ['FsSize', 'InstanceSize', 'TblspcSize', 'WalFilesSize']
      }]
    },
    methods: {
      isVisible: isVisible,
      setVisible: setVisible,
      selectAll: selectAll,
      unselectAll: unselectAll,
      removeGraph: removeGraph,
      loadGraphs: loadGraphs
    },
    watch: {
      graphs: function(val) {
        localStorage.setItem('graphs', JSON.stringify(val.map(function(item) {return item.id;})));
      }
    }
  });

  v.loadGraphs(JSON.parse(localStorage.getItem('graphs')) || v.themes[0].graphs);

  function newGraph(graph) {
    var id = graph.id;
    var picker = $('#daterange').data('daterangepicker');
    var startDate = picker.startDate;
    var endDate = picker.endDate;

    var defaultOptions = {
        axisLabelFontSize: 10,
        yLabelWidth: 14,
        legend: "always",
        labelsDiv: "legend"+id,
        labelsKMB: true,
        animatedZooms: true,
        gridLineColor: '#DDDDDD',
        dateWindow: [
          new Date(startDate).getTime(),
          new Date(endDate).getTime()
        ],
        xValueParser: function(x) {
          var m = moment(x);
          return m.toDate().getTime();
        },
        drawCallback: function(g, isInitial) {
          if (g.numRows() === 0) {
            $('#info'+id).html('<center><i>No data available</i></center>');
            $('#legend'+id).hide();
            $('#chart'+id).hide();
            $('#visibility'+id).hide();
          } else {
            addVisibilityCb(id, g, isInitial);
            $('#info'+id).html('');
            $('#legend'+id).show();
            $('#chart'+id).show();
            $('#visibility'+id).show();
          }
        },
        zoomCallback: function(minDate, maxDate, yRanges) {
          synchronizeZoom(minDate, maxDate);
        },
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
              synchronizeZoom(dates[0], dates[1]);
            } else if (context.isZooming) {
              Dygraph.endZoom(event, g, context);
              // don't do the same since zoom is animated
              // zoomCallback will do the job
            }
          }
        }
    };

    for (var attrname in graph.options) {
      defaultOptions[attrname] = metrics[id].options[attrname];
    }
    g = new Dygraph(
      document.getElementById("chart"+id),
      apiUrl+"/"+metrics[id].api+"?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1",
      defaultOptions
    );

    g.ready(function(g) {
      if (metrics[id].alertsApi) {
        loadAlerts(g, metrics[id].alertsApi);
      }
    });
    graph.chart = g;
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }

  function addVisibilityCb(chartId, g, isInitial) {
    if (!isInitial)
      return;

    var nbLegendItem = 0;
    var visibilityHtml = ''
    var cbIds = [];
    $('#legend'+chartId).children('span').each(function() {
      visibilityHtml += '<input type="checkbox" id="'+chartId+'CB'+nbLegendItem+'" checked>';
      visibilityHtml += '<label for="'+chartId+'CB'+nbLegendItem+'" style="'+$(this).attr('style')+'"> '+$(this).text()+'</label>  ';
      cbIds.push(chartId+'CB'+nbLegendItem);
      nbLegendItem++;
    });
    $('#visibility'+chartId).html(visibilityHtml);
    cbIds.forEach(function(id) {
      $('#'+id).change(function() {
        g.setVisibility(parseInt($(this).attr('id').replace(chartId+'CB', '')), $(this).is(':checked'));
      });
    })
  }


  function updateDateRange(start, end) {
    $('#daterange span').html(
      start.format(dateFormat) + ' - ' + end.format(dateFormat));
    window.location.hash = 'start=' + start + '&end=' + end;
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

  function synchronizeZoom(startDate, endDate, silent) {
    var picker = $('#daterange').data('daterangepicker');
    if (!silent) {
      // update picker
      picker.setStartDate(moment(startDate));
      picker.setEndDate(moment(endDate));
    }

    // get new date from picker (may be rounded)
    startDate = picker.startDate;
    endDate = picker.endDate;

    updateDateRange(startDate, endDate);

    v.graphs.forEach(function(graph) {
      var id = graph.id;
      var chart = graph.chart;
      // update the date range
      chart.updateOptions({
        dateWindow: [startDate, endDate]
      });
      // load the date for the given range
      chart.updateOptions({
        file: apiUrl+"/"+metrics[id].api+"?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1"
      }, false);
    });
  }

  // 'this' is the dygraph chart
  function loadAlerts(g, api) {
    var colors = {
      'OK': 'green',
      'WARNING': 'rgba(255, 120, 0, .2)',
      'CRITICAL': 'rgba(255, 0, 0, .2)'
    };
    $.ajax({
      url: alertingUrl+"/state_changes/" + api + ".json?start="+timestampToIsoDate(start)+"&end="+timestampToIsoDate(end)+"&noerror=1",
    }).success(function(data) {
      data = data.reverse();
      g.setAnnotations(data.map(function(alert) {
        var x = getClosestX(g, alert[0]);
        return {
          series: g.getLabels()[1],
          x: x,
          shortText: '♥',
          cssClass: 'alert-' + alert[1].toLowerCase(),
          text: alert[1],
          tickColor: colors[alert[1]],
          attachAtBottom: true
        }
      }));

      g.updateOptions({
        underlayCallback: function(canvas, area, g) {
          data.forEach(function(alert, index) {
            if (alert[1] == 'OK') {
              return;
            }

            var bottom_left = g.toDomCoords(new Date(alert[0]), 0);
            // Right boundary is next alert or end of visible series
            var right;
            if (index == data.length - 1) {
              var rows = g.numRows();
              right = g.getValue(rows - 1, 0);
            } else {
              right = new Date(data[index + 1][0]);
            }
            var top_right = g.toDomCoords(right, 10);
            var left = bottom_left[0];
            var right = top_right[0];

            canvas.fillStyle = colors[alert[1]];
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
  };
});
