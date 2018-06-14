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
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      async: true,
      contentType: "application/json",
      success: function (data) {
        $('#ErrorModal').modal('hide');
        updateDashboard(data, true);
        updateTps(data.databases);
        updateLoadaverage(data);
        updateNotifications(data.notifications);
      },
      error: function(xhr) {
        $('#ErrorModal').modal('hide');
        var code = xhr.status;
        var error = 'Internal error.';
        if (code > 0) {
          error = escapeHtml(JSON.parse(xhr.responseText).error);
        } else {
          code = '';
        }
        $('#modalError').html(html_error_modal(code, error));

        if (xhr.status == 401 || xhr.status == 302) {
          $('#ErrorModalFooter').html('<a class="btn btn-outline-secondary" id="aBackLogin">Back to login page</a>');
          $('#aBackLogin').attr('href', '/server/'+agent_address+'/'+agent_port+'/login');
        }
        $('#ErrorModal').modal('show');
      }
    });
  }

  function updateDashboard(data) {
    /** Update time **/
    $('#time').html(data['databases']['time']);
    $('#hostname').html(data['hostname']);
    $('#os_version').html(data['os_version']);
    $('#n_cpu').html(data['n_cpu']);
    $('#memory').html(filesize(data['memory']['total'] * 1000));
    $('#pg_version').html(data['pg_version']);
    $('#size').html(data['databases']['total_size']);
    $('#nb_db').html(data['databases']['databases']);
    $('#pg_data').html(data['pg_data']);
    $('#pg_port').html(data['pg_port']);
    $('#pg_uptime').html(data['pg_uptime']);

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
    var active_backends = data['active_backends']['nb'];
    sessionschart.data.datasets[0].data[0] = active_backends;
    sessionschart.data.datasets[0].data[1] = data['max_connections'] - active_backends;
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
    $('#total-hit').html(hitratiochart.data.datasets[0].data[0] + ' %');
  }

  function updateTotalSessions() {
    var data = sessionschart.data.datasets[0].data;
    var html = data[0];
    if (data[1]) {
      html += ' / ' + (data[0] + data[1]);
    }
    $('#total-sessions').html(html);
  }

  function updateLoadaverage(data) {
    /** Add the very new loadaverage value to the chart dataset ... **/
    var chart = loadaveragechart;
    chart.data.datasets[0].data.push(data['loadaverage']);
    chart.data.datasets[0].data.shift();
    $('#loadaverage').html(data['loadaverage']);
    chart.update();
  }

  function computeDelta(a, b, duration) {
    return Math.ceil((a - b) / duration);
  }

  function updateTps(data) {
    var chart = tpschart;
    var datasets = chart.data.datasets;
    var duration = data.timestamp - lastDatabasesDatum.timestamp;
    if (duration === 0) {
      return;
    }
    var deltaCommit = computeDelta(data.total_commit, lastDatabasesDatum.total_commit, duration);
    var deltaRollback = computeDelta(data.total_rollback, lastDatabasesDatum.total_rollback, duration);

    var commitData = datasets[0].data;
    commitData.push(deltaCommit);
    var rollbackData = datasets[1].data;
    rollbackData.push(deltaRollback);
    commitData.shift();
    rollbackData.shift();

    $('#tps_commit').html(deltaCommit);
    $('#tps_rollback').html(deltaRollback);
    chart.update();
    lastDatabasesDatum = data;
  }

  function updateNotifications(data) {
    var notif_html = '<ul class="notifications">';
    for (var i in data) {
      notif_html += '<li><span class="date-notification-db">'+data[i].date+'</span> <span class="badge badge-success">'+data[i].username+'</span> '+data[i].message+'</li>';
    }
    notif_html += '</ul>';
    $('#divNotif10').html(notif_html);
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

  var missingDataCount = config.history_length - jdata_history.length;
  if (missingDataCount > 0) {
    var missing = Array.apply(null, {length: missingDataCount});
    jdata_history = missing.concat(jdata_history);
  }

  var tpsData = jdata_history.map(function(a, index) {
    if (a === undefined) {
      return [null, null];
    }
    if (index === 0) {
      return [0, 0];
    }
    var curr = a.databases;
    var prev = jdata_history[index - 1];
    if (!prev) {
      return [null, null];
    }
    prev = prev.databases;
    var duration = curr.timestamp - prev.timestamp;
    var deltaCommit = computeDelta(curr.total_commit, prev.total_commit, duration);
    var deltaRollback = computeDelta(curr.total_rollback, prev.total_rollback, duration);
    return [deltaCommit, deltaRollback];
  });

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
        gridLines: {
          display: false
        },
        ticks: {
          display: false
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
        labels: Array.apply(null, Array(tpsData.length)),
        datasets : [
          {
            label: "Commit",
            backgroundColor: "rgba(0,188,18,0.2)",
            borderColor: "rgba(0,188,18,1)",
            data: tpsData.map(function(a) {return a[0]})
          },
          {
            label: "Rollback",
            backgroundColor: "rgba(188,0,0,0.2)",
            borderColor: "rgba(188,0,0,1)",
            data: tpsData.map(function(a) {return a[1]})
          }
        ]
      },
      options: lineChartsOptions
    }
  );

  var loadaverageData = jdata_history.map(function(item) {
    return item ? item.loadaverage : null;
  });
  var loadaveragechart = new Chart(
    $('#chart-loadaverage').get(0).getContext('2d'),
    {
      type: 'line',
      data: {
        labels: Array.apply(null, Array(jdata_history.length)),
        datasets : [
          {
            label: "Loadaverage",
            data: loadaverageData,
            backgroundColor: 'rgba(250, 164, 58, 0.2)',
            borderColor: 'rgba(250, 164, 58, 1)', //'#FAA43A'
          }
        ]
      },
      options: lineChartsOptions
    }
  );

  var refreshInterval = config.scheduler_interval * 1000;
  window.setInterval(refreshDashboard, refreshInterval);
  refreshDashboard();

  if ($('#divAlerts')) { // monitoring plugin enabled
    var alertRefreshInterval = 60 * 1000;
    window.setInterval(updateAlerts, alertRefreshInterval);
    updateAlerts();
  }
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
