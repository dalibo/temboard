/* global apiUrl, dateMath, rangeUtils, moment, Vue, Dygraph */
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

  /**
   * Parse location hash to get start and end date
   * If dates are not provided, falls back to the date range corresponding to
   * the last 24 hours.
   */
  var refreshTimeoutId;
  var refreshInterval = 60 * 1000;
  var fromPicker;
  var toPicker;
  var p = getHashParams();
  var start = p.start || 'now-24h';
  var end = p.end || 'now';
  start = dateMath.parse(start).isValid() ? start : moment(parseInt(start, 10));
  end = dateMath.parse(end).isValid() ? end : moment(parseInt(end, 10));

  var fromDate;
  var toDate;

  var pickerOptions = {
    singleDatePicker: true,
    timePicker: true,
    timePicker24Hour: true,
    timePickerSeconds: false
  };

  var metrics = {
    "Loadavg": {
      title: "Loadaverage",
      api: "loadavg",
      options: {
        colors: [colors.blue, colors.orange, colors.green],
        ylabel: "Loadaverage"
      },
      category: 'system'
    },
    "CPU": {
      title: "CPU Usage",
      api: "cpu",
      options: {
        colors: [colors.blue, colors.green, colors.red, colors.gray],
        ylabel: "%",
        stackedGraph: true
      },
      category: 'system'
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
      category: 'system'
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
      category: 'system'
    },
    "FsSize": {
      title: "Filesystems size",
      api: "fs_size",
      options: {
        ylabel: "Size",
        labelsKMB: false,
        labelsKMG2: true
      },
      category: 'system'
    },
    "FsUsage": {
      title: "Filesystems usage",
      api: "fs_usage",
      options: {
        ylabel: "%"
      },
      category: 'system'
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
      category: 'postgres'
    },
    "Blocks": {
      title: "Blocks Hit vs Read per second",
      api: "blocks",
      options: {
        colors: [colors.red, colors.green],
        ylabel: "Blocks"
      },
      category: 'postgres'
    },
    "HRR": {
      title: "Blocks Hit vs Read ratio",
      api: "hitreadratio",
      options: {
        colors: [colors.blue],
        ylabel: "%"
      },
      category: 'postgres'
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
      category: 'postgres'
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
      category: 'postgres'
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

  function selectAll() {
    loadGraphs(Object.keys(metrics));
  }

  function unselectAll() {
    loadGraphs([]);
  }

  function removeGraph(graph) {
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

    var startDate = dateMath.parse(rangePickerVue.from);
    var endDate = dateMath.parse(rangePickerVue.to, true);

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
            synchronizeZoom(dates[0], dates[1]);
          } else if (context.isZooming) {
            Dygraph.endZoom(event, g, context);
            // don't do the same since zoom is animated
            // zoomCallback will do the job
          }
        }
      }
    };

    for (var attrname in metrics[id].options) {
      defaultOptions[attrname] = metrics[id].options[attrname];
    }
    graph.chart = new Dygraph(
      document.getElementById("chart"+id),
      apiUrl+"/"+metrics[id].api+"?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1",
      defaultOptions
    );
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }

  function addVisibilityCb(chartId, g, isInitial) {
    if (!isInitial)
      return;

    var nbLegendItem = 0;
    var visibilityHtml = '';
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
    });
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
    rangePickerVue.from = moment(min);
    rangePickerVue.to = moment(max);
    rangePickerVue.editRawFrom = rangePickerVue.from.clone();
    rangePickerVue.editRawTo = rangePickerVue.to.clone();
    refreshDates();
  }

  function synchronizeZoom(startDate, endDate, silent) {
    if (!silent) {
      // update picker
      rangePickerVue.from = moment(startDate);
      rangePickerVue.to = moment(endDate);
      rangePickerVue.editRawFrom = rangePickerVue.from.clone();
      rangePickerVue.editRawTo = rangePickerVue.to.clone();
    }

    v.graphs.forEach(function(graph) {
      var id = graph.id;
      var chart = graph.chart;
      if (!chart) {
        return;
      }
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

  var rangePickerVue = new Vue({
    el: '#daterange',
    data: {
      ranges: rangeUtils.getRelativeTimesList(),
      rangeString: function() {
        return rangeUtils.describeTimeRange({from: this.from, to: this.to});
      },
      from: start,
      to: end,
      editRawFrom: null,
      editRawTo: null,
      isPickerOpen: false
    },
    computed: {
      autoRefresh: function() {
        return this.from.toString().indexOf('now') != -1 ||
          this.to.toString().indexOf('now') != -1;
      }
    },
    methods: {
      loadRangeShortcut: loadRangeShortcut,
      describeTimeRange: rangeUtils.describeTimeRange,
      showHidePicker: showHidePicker,
      pickerApply: pickerApply
    }
  });

  function loadRangeShortcut(range) {
    this.from = this.editRawFrom = range.from;
    this.to = this.editRawTo = range.to;
    this.isPickerOpen = false;
    refreshDates();
  }

  function showHidePicker() {
    // Make sure input values correspond to current from/to
    // especially when not applying picked dates
    this.editRawFrom = this.from;
    this.editRawTo = this.to;
    this.isPickerOpen = !this.isPickerOpen;
  }

  function pickerApply() {
    this.from = this.editRawFrom;
    this.to = this.editRawTo;
    this.isPickerOpen = false;
    refreshDates();
  }

  function refreshDates() {
    window.location.hash = 'start=' + rangePickerVue.from + '&end=' + rangePickerVue.to;
    try {
      fromDate = dateMath.parse(rangePickerVue.from);
      toDate = dateMath.parse(rangePickerVue.to, true);
    } catch(e) {
      // do nothing
    }
    synchronizeZoom(fromDate, toDate, true);
    window.clearTimeout(refreshTimeoutId);
    if (rangePickerVue.autoRefresh) {
      refreshTimeoutId = window.setTimeout(refreshDates, refreshInterval);
    }
    synchronizePickers();
  }

  /*
   * Make sure that date pickers are up-to-date
   * especially with any 'now-like' dates
   */
  function synchronizePickers() {
    // update 'from' date picker only if not currently open
    // and 'from' is updating (ie. contains 'now')
    if (!fromPicker || !fromPicker.data('daterangepicker').isShowing) {
      fromPicker = $('#fromPicker').daterangepicker(
        $.extend({
          startDate: dateMath.parse(rangePickerVue.editRawFrom)
        }, pickerOptions),
        onPickerApply
      );
    }
    // update 'to' date picker only if not currently open
    // and 'to' is updating (ie. contains 'now')
    if (!toPicker || !toPicker.data('daterangepicker').isShowing) {
      toPicker = $('#toPicker').daterangepicker(
        $.extend({
          startDate: dateMath.parse(rangePickerVue.editRawTo),
          minDate: dateMath.parse(rangePickerVue.editRawFrom)
        }, pickerOptions),
        onPickerApply
      );
    }
  }

  function onPickerApply(start) {
    var target = $(this.element).attr('data-target');
    rangePickerVue[target] = start;
    refreshDates();
  }

  refreshDates();
});
