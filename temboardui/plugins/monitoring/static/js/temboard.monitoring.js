$(function() {
  var dataApiUrl = apiUrl + "/data";
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
  var syncGraphs = [];

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
      dataApiUrl,
      true
    );
  });

  var graphs = [
    // System
    {
      id: "Loadavg",
      title: "Loadaverage",
      api: "loadavg",
      options: {
        colors: [colors.blue, colors.orange, colors.green],
        ylabel: "Loadaverage"
      }
    },
    {
      id: "CPU",
      title: "CPU Usage",
      api: "cpu",
      options: {
        colors: [colors.blue, colors.green, colors.red, colors.gray],
        ylabel: "%",
        stackedGraph: true
      }
    },
    {
      id: "CtxForks",
      title: "Context switches and forks per second",
      api: "ctxforks",
      options: {
        colors: [colors.blue, colors.green]
      }
    },
    {
      id: "Memory",
      title: "Memory usage",
      api: "memory",
      options: {
        colors: [colors.light_gray, colors.green, colors.blue, colors.orange],
        ylabel: "Memory",
        labelsKMB: false,
        labelsKMG2: true,
        stackedGraph: true
      }
    },
    {
      id: "Swap",
      title: "Swap usage",
      api: "swap",
      options: {
        colors: [colors.red],
        ylabel: "Swap",
        labelsKMB: false,
        labelsKMG2: true,
        stackedGraph: true
      }
    },
    {
      id: "FsSize",
      title: "Filesystems size",
      api: "fs_size",
      options: {
        ylabel: "Size",
        labelsKMB: false,
        labelsKMG2: true
      }
    },
    {
      id: "FsUsage",
      title: "Filesystems usage",
      api: "fs_usage",
      options: {
        ylabel: "%"
      }
    },
    // PostgreSQL
    {
      id: "TPS",
      title: "Transactions per second",
      api: "tps",
      options: {
        colors: [colors.green, colors.red],
        ylabel: "Transactions",
        stackedGraph: true
      }
    },
    {
      id: "InstanceSize",
      title: "Instance size",
      api: "instance_size",
      options: {
        colors: [colors.blue],
        ylabel: "Size",
        stackedGraph: true,
        labelsKMB: false,
        labelsKMG2: true
      }
    },
    {
      id: "TblspcSize",
      title: "Tablespaces size",
      api: "tblspc_size",
      options: {
        ylabel: "Size",
        stackedGraph: true,
        labelsKMB: false,
        labelsKMG2: true
      }
    },
    {
      id: "Sessions",
      title: "Sessions",
      api: "sessions",
      options: {
        ylabel: "Sessions",
        stackedGraph: true
      }
    },
    {
      id: "Blocks",
      title: "Blocks Hit vs Read per second",
      api: "blocks",
      options: {
        colors: [colors.red, colors.green],
        ylabel: "Blocks"
      }
    },
    {
      id: "HRR",
      title: "Blocks Hit vs Read ratio",
      api: "hitreadratio",
      options: {
        colors: [colors.blue],
        ylabel: "%"
      }
    },
    {
      id: "Checkpoints",
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
      }
    },
    {
      id: "WalFilesSize",
      title: "WAL Files size",
      api: "wal_files_size",
      options: {
        colors: [colors.blue, colors.blue2],
        labelsKMB: false,
        labelsKMG2: true,
        ylabel: "Size"
      }
    },
    {
      id: "WalFilesCount",
      title: "WAL Files",
      api: "wal_files_count",
      options: {
        colors: [colors.blue, colors.blue2],
        ylabel: "WAL files"
      }
    },
    {
      id: "WalFilesRate",
      title: "WAL Files written rate",
      api: "wal_files_rate",
      options: {
        colors: [colors.blue],
        ylabel: "Byte per second",
        labelsKMB: false,
        labelsKMG2: true,
        stackedGraph: true
      }
    },
    {
      id: "WBuffers",
      title: "Written buffers",
      api: "w_buffers",
      options: {
        ylabel: "Written buffers",
        stackedGraph: true
      }
    },
    {
      id: "Locks",
      title: "Locks",
      api: "locks",
      options: {
        ylabel: "Locks"
      }
    },
    {
      id: "WLocks",
      title: "Waiting Locks",
      api: "waiting_locks",
      options: {
        ylabel: "Waiting Locks"
      }
    }
  ];

  graphs.forEach(function(graph) {
    syncGraphs.push({
      dygraph: newGraph(graph.id, graph.title, graph.api, dataApiUrl, graph.options, start, end),
      api: graph.api
    });
  });

  function newGraph(id, title, api, apiUrl, options, startDate, endDate) {
    var html = '';
    html += '<div class="card">';
    html += ' <div class="card-header">';
    html += title;
    html += ' </div>';
    html += ' <div class="card-body">';
    html += '   <div id="info'+id+'"></div>';
    html += '   <div id="legend'+id+'" class="legend-chart"><div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Loading, please wait ...</div></div></div></div></div>';
    html += '   <div id="chart'+id+'" class="monitoring-chart"></div>';
    html += '   <div id="visibility'+id+'" class="visibility-chart"></div>';
    html += ' </div>';
    html += '</div>';
    $('#'+id).html(html);
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
          synchronizeZoom(minDate, maxDate, apiUrl);
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
              synchronizeZoom(dates[0], dates[1], apiUrl);
            } else if (context.isZooming) {
              Dygraph.endZoom(event, g, context);
              // don't do the same since zoom is animated
              // zoomCallback will do the job
            }
          }
        }
    };

    for (var attrname in options) {
      defaultOptions[attrname] = options[attrname];
    }
    var g = new Dygraph(
      document.getElementById("chart"+id),
      apiUrl+"/"+api+"?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1",
      defaultOptions
    );
    return g;
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

  function synchronizeZoom(startDate, endDate, apiUrl, silent) {
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

    syncGraphs.forEach(function(graph) {
      // update the date range
      graph.dygraph.updateOptions({
        dateWindow: [startDate, endDate]
      });
      // load the date for the given range
      graph.dygraph.updateOptions({
        file: apiUrl+"/"+graph.api+"?start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate)+"&noerror=1"
      }, false);
    });
  }
});
