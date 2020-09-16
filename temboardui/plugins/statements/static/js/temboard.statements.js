/* global Vue */
$(function() {
  "use strict";

  var dataRequest;
  var chartRequest;

  var v = new Vue({
    el: '#app',
    router: new VueRouter(),
    data: {
      statements: [],
      metas: null,
      lastSnapshot: null,
      isLoading: true,
      dbid: null,
      queryid: null,
      userid: null,
      datname: null,
      sortBy: 'total_exec_time',
      filter: '',
      from: null,
      to: null,
      totalRows: 1,
      currentPage: 1,
      perPage: 20
    },
    computed: {
      fields: getFields,
      fromTo: function() {
        return '' + this.from + this.to;
      },
      queryidUserid: function() {
        return this.queryid, this.userid;
      }
    },
    methods: {
      fetchData: fetchData,
      highlight: highlight,
      onFiltered: onFiltered
    },
    watch: {
      fromTo: fetchData,
      dbid: function() {
        var newQueryParams = _.assign({}, this.$route.query);
        if (!this.dbid) {
          delete newQueryParams.dbid;
          delete newQueryParams.queryid;
          delete newQueryParams.userid;
        } else {
          newQueryParams.dbid = this.dbid;
        }
        this.$router.push({ query: newQueryParams });
        this.fetchData();
      },
      queryidUserid: function() {
        var newQueryParams = _.assign({}, this.$route.query);
        if (!this.queryid) {
          delete newQueryParams.queryid;
          delete newQueryParams.userid;
        } else {
          newQueryParams.dbid = this.dbid;
          newQueryParams.queryid = this.queryid;
          newQueryParams.userid = this.userid;
        }
        this.$router.push({ query: newQueryParams });
        this.fetchData();
      },
      $route: function(to, from) {
        this.dbid = to.query.dbid;
        this.queryid = to.query.queryid;
        this.userid = to.query.userid;
      }
    }
  });

  function fetchData() {
    this.statements = [];
    var startDate = this.from;
    var endDate = this.to;

    var url = this.dbid ? '/' + this.dbid : '';
    url += this.queryid ? '/' + this.queryid : '';
    url += this.userid ? '/' + this.userid : '';

    this.isLoading = true;
    dataRequest && dataRequest.abort();
    dataRequest = $.get(
      apiUrl + url,
      {
        start: timestampToIsoDate(startDate),
        end: timestampToIsoDate(endDate),
        noerror: 1
      },
      function(data) {
        this.isLoading = false;
        this.datname = data.datname;
        this.statements = data.data;
        // automatically show detail if a single query is displayed
        if (this.queryid) {
          this.statements[0]._showDetails = true;
        }
        this.totalRows = this.statements.length;

        this.metas = data.metas;
      }.bind(this)
    );

    chartRequest && chartRequest.abort();
    chartRequest = $.get(
      chartApiUrl + url,
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
      key: 'total_exec_time',
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

  function onFiltered(filteredItems) {
    this.totalRows = filteredItems.length;
    this.currentPage = 1;
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }

  function createOrUpdateCharts(data) {
    var startDate = v.from;
    var endDate = v.to;
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
    v.$refs.daterangepicker.setFromTo(moment(min), moment(max));
  }

  v.dbid = v.$route.query.dbid;
  v.queryid = v.$route.query.queryid;
  v.userid = v.$route.query.userid;
});
