/* global Vue, moment */
$(function() {
  "use strict";

  function html_error_modal(code, error) {
    var html = '<div class="modal" id="ErrorModal" tabindex="-1" role="dialog" aria-labelledby="ErrorModalLabel" aria-hidden="true">';
    html += '   <div class="modal-dialog">';
    html += '     <div class="modal-content">';
    html += '       <div class="modal-header">';
    html += '         <h4 class="modal-title" id="ErrorModalLabel">Error '+code+'</h4>';
    html += '         <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
    html += '       </div>';
    html += '       <div class="modal-body">';
    html += '         <div class="alert alert-danger" role="alert">'+error+'</div>';
    html += '       </div>';
    html += '       <div class="modal-footer" id="ErrorModalFooter">';
    html += '         <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Close</button>';
    html += '       </div>';
    html += '     </div>';
    html += '   </div>';
    html += '</div>';
    return html;
  }

  /*
   * Call the agent's dashboard API and update the view through
   * updateDashboard() callback.
   */
  function refreshDashboard() {
    $.ajax({
      url: '/proxy/'+agent_address+'/'+agent_port+'/dashboard',
      type: 'GET',
      async: true,
      contentType: "application/json",
      success: function (data) {
        $('#ErrorModal').modal('hide');
        updateDashboard(data, true);
        updateTps([data]);
        updateLoadaverage([data]);
      },
      error: function(xhr) {
        $('#ErrorModal').modal('hide');
        if (xhr.status == 401 || xhr.status == 302) {
          // force a reload of the page, should lead to the server login page
          location.href = location.href;
        }
        var code = xhr.status;
        var error = 'Internal error.';
        if (code > 0) {
          error = escapeHtml(JSON.parse(xhr.responseText).error);
        } else {
          code = '';
        }
        $('#modalError').html(html_error_modal(code, error));
        $('#ErrorModal').modal('show');
      }
    });
  }

  function updateDashboard(data) {
    /** Update time **/
    $('#hostname').html(data['hostname']);
    $('#os_version').html(data['os_version']);
    $('#n_cpu').html(data['n_cpu']);
    $('#memory').html(filesize(data['memory']['total'] * 1000));
    $('#pg_version').html(data['pg_version'] || null);
    var databases = data['databases'];
    $('#size').html(databases ? databases.total_size : null);
    $('#nb_db').html(databases ? databases.databases : null);
    $('#pg_data').html(data['pg_data']);
    $('#pg_port').html(data['pg_port']);
    $('#pg_uptime').html(data['pg_uptime'] || 'N/A');

    /** Update memory usage chart **/
    memorychart.data.datasets[0].data[0] = data['memory']['active'];
    memorychart.data.datasets[0].data[1] = data['memory']['cached'];
    memorychart.data.datasets[0].data[2] = data['memory']['free'];
    memorychart.update();
    updateTotalMemory();

    /** Update CPU usage chart **/
    cpuchart.data.datasets[0].data[0] = data['cpu']['iowait'];
    cpuchart.data.datasets[0].data[1] = data['cpu']['steal'];
    cpuchart.data.datasets[0].data[2] = data['cpu']['user'];
    cpuchart.data.datasets[0].data[3] = data['cpu']['system'];
    cpuchart.data.datasets[0].data[4] = data['cpu']['idle'];
    cpuchart.update();
    updateTotalCpu();

    /** Hitratio chart **/
    hitratiochart.data.datasets[0].data[0] = data['hitratio'];
    hitratiochart.data.datasets[0].data[1] = (100 - data['hitratio']);
    hitratiochart.update();
    updateTotalHit();

    /** Sessions chart **/
    var active_backends = data.active_backends;
    var nb_active_backends = active_backends ? active_backends.nb : null;
    sessionschart.data.datasets[0].data[0] = nb_active_backends;
    sessionschart.data.datasets[0].data[1] = data['max_connections'] - nb_active_backends;
    sessionschart.update();
    updateTotalSessions();
  }

  function updateTotalCpu() {
    var totalCpu = 0;
    // create a copy of data
    var data = cpuchart.data.datasets[0].data.slice(0);
    // last element is "idle", don't take it into account
    data.pop();
    var totalCpu = data.reduce(function(a, b) {return a + b;}, 0);
    $('#total-cpu').html(parseInt(totalCpu) + ' %');
  }

  function updateTotalMemory() {
    var totalMemory = 0;
    // create a copy of data
    var data = memorychart.data.datasets[0].data.slice(0);
    // last element is "Free", don't take it into account
    data.pop();
    var totalMemory = data.reduce(function(a, b) {return a + b;}, 0);
    $('#total-memory').html(parseInt(totalMemory) + ' %');
  }

  function updateTotalHit() {
    var totalHit = hitratiochart.data.datasets[0].data[0];
    $('#total-hit').html(totalHit ? totalHit + ' %' : 'N/A');
  }

  function updateTotalSessions() {
    var data = sessionschart.data.datasets[0].data;
    var html = data[0];
    if (data[1]) {
      html += ' / ' + (data[0] + data[1]);
    }
    $('#total-sessions').html(html);
  }

  function updateTimeRange(chart) {
    // update date range
    var timeConfig = chart.options.scales.xAxes[0].time;
    var now = moment();
    timeConfig.min = now.clone().subtract(timeRange, 's');
    timeConfig.max = now;

    // Remove old data
    var datasets = chart.data.datasets;
    for (var i = 0; i < datasets.length; i++) {
      var dataset = datasets[i];
      dataset.data = dataset.data.filter(function(datum) {
        return datum.x > moment(chart.options.scales.xAxes[0].time.min).unix() * 1000;
      });
    }
    chart.update();
  }

  function updateLoadaverage(data) {
    /** Add the very new loadaverage value to the chart dataset ... **/
    var chart = loadaveragechart;
    updateTimeRange(chart);

    for (var i = 0; i < data.length; i++) {
      chart.data.datasets[0].data.push({
        x: data[i].timestamp * 1000,
        y: data[i].loadaverage
      });
    }
    $('#loadaverage').html(data[data.length - 1]['loadaverage']);
    chart.update();
  }

  function computeDelta(a, b, duration) {
    return Math.ceil((a - b) / duration);
  }

  var lastDatabasesDatum = {};

  function updateTps(data) {
    var chart = tpschart;
    updateTimeRange(chart);

    var datasets = chart.data.datasets;
    var commitData = datasets[0].data;
    var rollbackData = datasets[1].data;

    var i = 0;
    var len = data.length;
    var timestamp;
    var duration;
    for (i; i < len; i++) {
      var datum = data[i];
      var databases = datum.databases;
      if (!databases) {
        commitData.push({x: datum.timestamp * 1000, y: NaN});
        rollbackData.push({x: datum.timestamp * 1000, y: NaN});
        lastDatabasesDatum = {
          total_commit: NaN,
          total_rollback: NaN,
          timestamp: datum.timestamp
        };
      } else {
        var duration = databases.timestamp - lastDatabasesDatum.timestamp;
        if (duration === 0) {
          continue;
        }
        var deltaCommit = computeDelta(databases.total_commit, lastDatabasesDatum.total_commit, duration);
        var deltaRollback = computeDelta(databases.total_rollback, lastDatabasesDatum.total_rollback, duration);

        commitData.push({x: databases.timestamp * 1000, y: deltaCommit});
        rollbackData.push({x: databases.timestamp * 1000, y: deltaRollback});
        lastDatabasesDatum = databases;
      }
    }

    $('#tps_commit').html(commitData[commitData.length -1].y);
    $('#tps_rollback').html(rollbackData[rollbackData.length - 1].y);
    chart.update();

    $('#postgres-stopped-msg').toggleClass('d-none', !!data[data.length - 1].databases);
  }

  var alertsView = new Vue({
    el: '#divAlerts',
    data: {
      alerts: [],
      states: [],
      moment: moment
    },
    methods: {
      getBorderColor: function(state) {
        if (state != 'OK' && state != 'UNDEF') {
          return 'border border-2 border-' + state.toLowerCase();
        }
        return 'border border-light';
      }
    }
  });

  /**
   * Update status and alerts
   */
  function updateAlerts() {
    $.ajax({
      url: '/server/'+agent_address+'/'+agent_port+'/alerting/alerts.json',
    }).success(function(data) {
      // remove any previous popover to avoid conflicts with
      // recycled div elements
      $('#divAlerts [data-toggle-popover]').popover('dispose');
      alertsView.alerts = data;
      window.setTimeout(function() {
        $('#divAlerts [data-toggle-popover]').popover({
          placement: 'top',
          container: 'body',
          boundary: 'window',
          content: function() {
            return $(this).find('.popover-content')[0].outerHTML.replace('d-none', '');
          },
          html: true
        });
      }, 1);
    }).error(function(error) {
      // FIXME handle error
      console.error(error);
    });

    $.ajax({
      url: '/server/'+agent_address+'/'+agent_port+'/alerting/checks.json',
    }).success(function(data) {
      alertsView.states = data;
    }).error(function(error) {
      // FIXME handle error
      console.error(error);
    });

  }

  var options = {
    responsive : true,
    maintainAspectRatio: false,
    legend: false,
    rotation: Math.PI,
    circumference: Math.PI
  };

  var memorychart = new Chart(
    $('#chart-memory').get(0).getContext('2d'),
    {
      type: 'doughnut',
      data: {
        labels: ["Active", "Cached", "Free"],
        datasets: [
          {
            backgroundColor: ["#cc2936", "#29cc36","#eeeeee"]
          }
        ]
      },
      options: options
    }
  );

  var cpuchart = new Chart(
    $('#chart-cpu').get(0).getContext('2d'),
    {
      type: 'doughnut',
      data: {
        labels: ["IO Wait", "Steal", "User", "System", "IDLE"],
        datasets: [
          {
            backgroundColor: ["#cc2936", "#cbff00", "#29cc36", "#cbff00", "#eeeeee"]
          }
        ]
      },
      options: options
    }
  );

  var hitratiochart = new Chart(
    $('#chart-hitratio').get(0).getContext('2d'),
    {
      type: 'doughnut',
      data: {
        labels: ["Hit", "Read"],
        datasets: [
          {
            backgroundColor: ["#29cc36", "#cc2936"]
          }
        ]
      },
      options: options
    }
  );

  var sessionschart = new Chart(
    $('#chart-sessions').get(0).getContext('2d'),
    {
      type: 'doughnut',
      data: {
        labels: ["Active backends", "Free"],
        datasets: [
          {
            backgroundColor: ["#29cc36", "#eeeeee"]
          }
        ]
      },
      options: options
    }
  );
  updateTotalSessions();

  var now = moment();
  var timeRange = config.history_length * config.scheduler_interval;

  var lineChartsOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    legend: {
      display: false
    },
    scales: {
      yAxes: [{
        ticks: {
          beginAtZero: true
        }
      }],
      xAxes: [{
        type: 'time',
        time: {
          min: now.clone().subtract(timeRange, 's'),
          max: now,
          displayFormats: {
            second: 'h:mm a',
            minute: 'h:mm a'
          }
        }
      }]
    },
    elements: {
      point: {
        radius: 0,
        hoverRadius: 0
      },
      line: {
        borderWidth: 1
      }
    },
    tooltips: {
      enabled: false
    }
  };

  var tpschart = new Chart(
    $('#chart-tps').get(0).getContext('2d'),
    {
      type: 'line',
      data: {
        datasets : [
          {
            label: "Commit",
            backgroundColor: "rgba(0,188,18,0.2)",
            borderColor: "rgba(0,188,18,1)"
          },
          {
            label: "Rollback",
            backgroundColor: "rgba(188,0,0,0.2)",
            borderColor: "rgba(188,0,0,1)"
          }
        ]
      },
      options: lineChartsOptions
    }
  );
  updateTps(jdata_history);

  var loadaveragechart = new Chart(
    $('#chart-loadaverage').get(0).getContext('2d'),
    {
      type: 'line',
      data: {
        datasets : [
          {
            label: "Loadaverage",
            backgroundColor: 'rgba(250, 164, 58, 0.2)',
            borderColor: 'rgba(250, 164, 58, 1)', //'#FAA43A'
          }
        ]
      },
      options: lineChartsOptions
    }
  );
  updateLoadaverage(jdata_history);

  var refreshInterval = config.scheduler_interval * 1000;
  window.setInterval(refreshDashboard, refreshInterval);
  refreshDashboard();

  if ($('#divAlerts')) { // monitoring plugin enabled
    var alertRefreshInterval = 60 * 1000;
    window.setInterval(updateAlerts, alertRefreshInterval);
    updateAlerts();
  }

  $('.fullscreen').on('click', function(e) {
    e.preventDefault();
    $(this).addClass('d-none');
    const el = $(this).parents('.main')[0];
    fscreen.requestFullscreen(el);
  });

  fscreen.onfullscreenchange = function onFullScreenChange(event) {
    if (!fscreen.fullscreenElement) {
      $('.fullscreen').removeClass('d-none');
    }
  }

  // hide fullscreen button if not supported
  $('.fullscreen').toggleClass('d-none', !fscreen.fullscreenEnabled);
});

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
