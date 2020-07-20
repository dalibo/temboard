/* global Vue */
$(function() {
  "use strict";

  var refreshTimeoutId;
  var refreshInterval = 60 * 1000;

  var v = new Vue({
    el: '#app',
    router: new VueRouter(),
    data: {
      statements: [],
      metas: null,
      lastSnapshot: null,
      isLoading: true,
      dbid: null,
      datname: null,
      sortBy: 'total_time',
      filter: '',
      from: null,
      to: null
    },
    computed: {
      fields: getFields,
      fromTo: function() {
        return this.from, this.to, new Date();
      }
    },
    methods: {
      fetchData: fetchData,
      onPickerUpdate: onPickerUpdate,
      highlight: highlight
    },
    watch: {
      fromTo: function() {
        this.$router.replace({ query: _.assign({}, this.$route.query, {
          start: '' + v.from,
          end: '' + v.to
        })});
        this.fetchData();
      },
      dbid: function() {
        var newQueryParams = _.assign({}, this.$route.query);
        if (!this.dbid) {
          delete newQueryParams.dbid;
        } else {
          newQueryParams.dbid = this.dbid;
        }
        this.$router.replace({ query: newQueryParams });
        this.fetchData();
      }
    }
  });

  var start = v.$route.query.start || 'now-24h';
  var end = v.$route.query.end || 'now';
  v.from = start;
  v.to = end;

  function fetchData() {
    this.statements = [];
    var startDate = dateMath.parse(this.from);
    var endDate = dateMath.parse(this.to, true);

    this.isLoading = true;
    $.get(
      apiUrl + (this.dbid ? '/' + this.dbid : ''),
      {
        start: timestampToIsoDate(startDate),
        end: timestampToIsoDate(endDate),
        noerror: 1
      },
      function(data) {
        this.isLoading = false;
        this.datname = data.datname;
        this.statements = data.data;

        this.metas = data.metas;

        window.clearTimeout(refreshTimeoutId);
        if (this.from.toString().indexOf('now') != -1 ||
            this.to.toString().indexOf('now') != -1) {
          refreshTimeoutId = window.setTimeout(fetchData.bind(this), refreshInterval);
        }
      }.bind(this)
    );

    $.get(
      chartApiUrl + (this.dbid ? '/' + this.dbid : ''),
      {
        start: timestampToIsoDate(startDate),
        end: timestampToIsoDate(endDate),
        noerror: 1
      },
      createOrUpdateCharts
    );
  }

  function getFields() {
    var fields = [{
      key: 'query',
      label: 'Query',
      class: 'query',
      sortable: true,
      sortDirection: 'asc'
    }, {
      key: 'datname',
      label: 'DB',
      sortable: true,
      sortDirection: 'asc'
    }, {
      key: 'rolname',
      label: 'User',
      sortable: true,
      sortDirection: 'asc'
    }, {
      key: 'calls',
      label: 'Calls',
      class: 'text-right',
      sortable: true
    }, {
      key: 'total_time',
      label: 'Total',
      formatter: formatDuration,
      class: 'text-right border-left',
      sortable: true
    }, {
      key: 'mean_time',
      label: 'AVG',
      formatter: formatDuration,
      class: 'text-right',
      sortable: true
    }, {
      key: 'shared_blks_read',
      label: 'Read',
      class: 'text-right border-left',
      formatter: formatSize,
      sortable: true
    }, {
      key: 'shared_blks_hit',
      label: 'Hit',
      class: 'text-right',
      formatter: formatSize,
      sortable: true
    }, {
      key: 'shared_blks_dirtied',
      label: 'Dirt.',
      class: 'text-right',
      formatter: formatSize,
      sortable: true
    }, {
      key: 'shared_blks_written',
      label: 'Writ.',
      class: 'text-right',
      formatter: formatSize,
      sortable: true
    }, {
      key: 'temp_blks_read',
      label: 'Read',
      class: 'text-right border-left',
      formatter: formatSize,
      sortable: true
    }, {
      key: 'temp_blks_written',
      label: 'Writ.',
      class: 'text-right',
      formatter: formatSize,
      sortable: true
    }];

    var ignored = ['rolname', 'query'];
    if (this.dbid) {
      ignored = ['datname'];
    }

    return _.filter(fields, function(field) {
      return ignored.indexOf(field.key) === -1;
    });
  }

  function formatDuration(value) {
    return moment(parseFloat(value, 10)).preciseDiff(moment(0), 1);
  }

  function formatSize(bytes) {
    bytes *= 8192;
    var sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '<span class="text-muted">0</span>';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
  }

  function highlight(src) {
    return hljs.highlight('sql', src).value;
  }

  function onPickerUpdate(from, to) {
    this.from = from;
    this.to = to;
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }

  function createOrUpdateCharts(data) {
    var startDate = dateMath.parse(v.from);
    var endDate = dateMath.parse(v.to, true);
    var defaultOptions = {
      axisLabelFontSize: 10,
      yLabelWidth: 14,
      includeZero: true,
      legend: 'always',
      labelsKMB: true,
      gridLineColor: 'rgba(128, 128, 128, 0.3)',
      dateWindow: [
        new Date(startDate).getTime(),
        new Date(endDate).getTime()
      ],
      xValueParser: function(x) {
        var m = moment(x);
        return m.toDate().getTime();
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

    var chart = this.chart;

    var chart1Data = _.map(data.data, function(datum) {
      return [
        moment.unix(datum.ts).toDate(),
        datum.calls
      ];
    });
    new Dygraph(
      document.getElementById('chart1'),
      chart1Data,
      Object.assign({}, defaultOptions, {
        labels: ['time', 'Queries per sec'],
        labelsDiv: 'legend-chart1'
      })
    );

    var chart2Data = _.map(data.data, function(datum) {
      return [
        moment.unix(datum.ts).toDate(),
        datum.load,
        datum.avg_runtime
      ];
    });
    new Dygraph(
      document.getElementById('chart2'),
      chart2Data,
      Object.assign({}, defaultOptions, {
        labels: ['time', 'Time per sec', 'Avg runtime'],
        labelsDiv: 'legend-chart2',
        axes: {
          y: {
            valueFormatter: formatDuration,
            axisLabelFormatter: formatDuration
          }
        }
      })
    );

    var chart3Data = _.map(data.data, function(datum) {
      return [
        moment.unix(datum.ts).toDate(),
        datum.total_blks_hit,
        datum.total_blks_read
      ];
    });
    new Dygraph(
      document.getElementById('chart3'),
      chart3Data,
      Object.assign({}, defaultOptions, {
        labels: ['time', 'Hit /s', 'Read /s'],
        labelsDiv: 'legend-chart3',
        axes: {
          y: {
            valueFormatter: formatSize,
            axisLabelFormatter: formatSize
          }
        }
      })
    );
  }

  function onChartZoom(min, max) {
    v.from = moment(min);
    v.to = moment(max);
  }

  /**
   * Parse location to get start and end date
   * If dates are not provided, falls back to the date range corresponding to
   * the last 24 hours.
   */
  var start = v.$route.query.start || 'now-24h';
  var end = v.$route.query.end || 'now';
  start = dateMath.parse(start).isValid() ? start : moment(parseInt(start, 10));
  end = dateMath.parse(end).isValid() ? end : moment(parseInt(end, 10));

  v.from = start;
  v.to = end;
  v.dbid = v.$route.query.dbid;
});
