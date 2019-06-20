import 'bootstrap';
import * as _ from 'lodash';
import moment from 'moment';
import Vue from 'vue';
import VueRouter from 'vue-router';
import * as dateMath from './datemath.js';
import './daterangepicker.vue.js';
import draggable from 'vuedraggable';
import Dygraph from 'dygraphs';

require('base');

Vue.use(VueRouter);

/* global apiUrl, dateMath, moment, Vue, VueRouter, Dygraph */
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

  var refreshTimeoutId;
  var refreshInterval = 60 * 1000;

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
    props: ['graph', 'from', 'to'],
    mounted: function() {
      createOrUpdateChart.call(this, true);
    },
    watch: {
      graph: function() {
        // recreate the chart if metric changes
        createOrUpdateChart.call(this, true);
      },
      // only one watcher for from + to
      fromTo: function() {
        createOrUpdateChart.call(this, false);
      }
    },
    computed: {
      fromTo: function() {
        return this.from, this.to, new Date();
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
    updateLocalStorage.call(this);
  }

  function selectAll() {
    loadGraphs(Object.keys(metrics));
    updateLocalStorage.call(this);
  }

  function unselectAll() {
    loadGraphs([]);
    updateLocalStorage.call(this);
  }

  function updateLocalStorage() {
    var graphs = JSON.stringify(this.graphs.map(function(item) {return item.id;}))
    localStorage.setItem('graphs', graphs);
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
    router: new VueRouter(),
    data: {
      // each graph is an Object with id and chart properties
      graphs: [],
      from: null,
      to: null,
      fromDate: null,
      toDate: null,
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
      loadGraphs: loadGraphs,
      onPickerUpdate: onPickerUpdate
    },
    computed: {
      fromTo: function() {
        return this.from, this.to, new Date();
      }
    },
    components: {
      draggable: draggable
    },
    watch: {
      graphs: function(val) {
        var graphs = JSON.stringify(val.map(function(item) {return item.id;}))
        this.$router.replace({ query: _.assign({}, this.$route.query, {
          graphs: graphs
        })});
      },
      fromTo: function() {
        this.$router.replace({ query: _.assign({}, this.$route.query, {
          start: '' + v.from,
          end: '' + v.to
        })});
      },
    }
  });

  /**
   * Parse location to get start and end date
   * If dates are not provided, falls back to the date range corresponding to
   * the last 24 hours.
   */
  var start = v.$route.query.start || 'now-24h';
  var end = v.$route.query.end || 'now';
  start = dateMath.parse(start).isValid() ? start : moment(parseInt(start, 10));
  end = dateMath.parse(end).isValid() ? end : moment(parseInt(end, 10));

  var graphs = v.$route.query.graphs;
  graphs = graphs ? JSON.parse(graphs) : (JSON.parse(localStorage.getItem('graphs')) || v.themes[0].graphs);
  v.loadGraphs(graphs);

  function createOrUpdateChart(create) {
    var id = this.graph.id;

    var startDate = dateMath.parse(v.fromDate);
    var endDate = dateMath.parse(v.toDate, true);

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
        addVisibilityCb(id, g, isInitial);
        if (g.numRows() === 0) {
          $('#nodata'+id).removeClass('d-none');
        } else {
          $('#nodata'+id).addClass('d-none');
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
            onChartZoom(dates[0], dates[1]);
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

    var params = "?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1";
    var data = null;
    var dataReq = $.get(apiUrl+"/"+metrics[id].api+params, function(_data) {
      data = _data;
    });
    // Get the dates when the instance was unavailable
    var unavailabilityData = '';
    var promise = $.when(dataReq);
    if (metrics[id].category == 'postgres') {
      promise = $.when(dataReq,
        $.get(unavailabilityUrl + params, function(_data) { unavailabilityData = _data; })
      );
    }
    promise.then(function() {
      // fill unavailability data with NaN
      var colsCount = data.split('\n')[0].split(',').length;
      var nanArray = new Array(colsCount - 1).fill('NaN');
      nanArray.unshift('');
      unavailabilityData = unavailabilityData.replace(/\n/g, nanArray.join(',') + '\n');

      // do the job when all ajax request have succeeded
      if (!this.graph.chart || create) {
        this.graph.chart = new Dygraph(
          document.getElementById("chart"+id),
          data + unavailabilityData,
          defaultOptions
        );
      } else {
        this.graph.chart.ready(function() {
          // update the date range
          this.graph.chart.updateOptions({
            dateWindow: [startDate, endDate]
          });

          // load the data for the given range
          this.graph.chart.updateOptions({
            file: data + unavailabilityData
          }, false);
        }.bind(this));
      }
    }.bind(this));
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

  function onChartZoom(min, max) {
    v.from = moment(min);
    v.to = moment(max);
    refreshDates();
  }

  function onPickerUpdate(from, to) {
    this.from = from;
    this.to = to;
    refreshDates();
  }

  function refreshDates() {
    v.fromDate = dateMath.parse(v.from);
    v.toDate = dateMath.parse(v.to, true);
    window.clearTimeout(refreshTimeoutId);
    if (v.from.toString().indexOf('now') != -1 ||
        v.to.toString().indexOf('now') != -1) {
      refreshTimeoutId = window.setTimeout(refreshDates, refreshInterval);
    }
  }
  v.from = start;
  v.to = end;
  refreshDates();
});
