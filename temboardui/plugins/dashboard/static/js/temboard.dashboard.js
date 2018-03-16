var last_update_timestamp = 0;

function html_error_modal(code, error) {
  var error_html = '';
  error_html += '<div class="modal" id="ErrorModal" tabindex="-1" role="dialog" aria-labelledby="ErrorModalLabel" aria-hidden="true">';
  error_html += '   <div class="modal-dialog">';
  error_html += '     <div class="modal-content">';
  error_html += '       <div class="modal-header">';
  error_html += '         <h4 class="modal-title" id="ErrorModalLabel">Error '+code+'</h4>';
  error_html += '         <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
  error_html += '       </div>';
  error_html += '       <div class="modal-body">';
  error_html += '         <div class="alert alert-danger" role="alert">'+error+'</div>';
  error_html += '       </div>';
  error_html += '       <div class="modal-footer" id="ErrorModalFooter">';
  error_html += '         <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Close</button>';
  error_html += '       </div>';
  error_html += '     </div>';
  error_html += '   </div>';
  error_html += '</div>';
  return error_html;
}

/*
 * Call the agent's dashboard API and update the view through
 * update_dashboard() callback.
 */
function refreshDashboard() {
  $.ajax({
    url: '/proxy/'+agent_address+'/'+agent_port+'/dashboard',
    type: 'GET',
    beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
    async: true,
    contentType: "application/json",
    success: function (data) {
      if (data['databases']['timestamp'] != last_update_timestamp)
      {
        $('#ErrorModal').modal('hide');
        last_update_timestamp = data['databases']['timestamp'];
        update_dashboard(data, true);
        updateTps(data.databases);
        updateLoadaverage(data);
        update_notifications(data.notifications);
      }
    },
    error: function(xhr) {
      if (xhr.status == 401)
      {
        $('#ErrorModal').modal('hide');
        $('#modalError').html(html_error_modal(401, 'Session expired'));
        $('#ErrorModalFooter').html('<a class="btn btn-outline-secondary" id="aBackLogin">Back to login page</a>');
        $('#aBackLogin').attr('href', '/server/'+agent_address+'/'+agent_port+'/login');
        $('#ErrorModal').modal('show');
      }
      else
      {
        $('#ErrorModal').modal('hide');
        var code = xhr.status;
        var error = 'Internal error.';
        if (code > 0)
        {
          error = escapeHtml(JSON.parse(xhr.responseText).error);
        } else {
          code = '';
        }
        $('#modalError').html(html_error_modal(code, error));
        $('#ErrorModal').modal('show');
      }
    }
  });
}
window.setInterval(refreshDashboard, 2000);

function update_dashboard(data)
{
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
  window.memorychart.data.datasets[0].data[0] = data['memory']['active'];
  window.memorychart.data.datasets[0].data[1] = data['memory']['cached'];
  window.memorychart.data.datasets[0].data[2] = data['memory']['free'];
  window.memorychart.update();
  update_total_memory();

  /** Update CPU usage chart **/
  window.cpuchart.data.datasets[0].data[0] = data['cpu']['iowait'];
  window.cpuchart.data.datasets[0].data[1] = data['cpu']['steal'];
  window.cpuchart.data.datasets[0].data[2] = data['cpu']['user'];
  window.cpuchart.data.datasets[0].data[3] = data['cpu']['system'];
  window.cpuchart.data.datasets[0].data[4] = data['cpu']['idle'];
  window.cpuchart.update();
  update_total_cpu();

  /** Hitratio chart **/
  window.hitratiochart.data.datasets[0].data[0] = data['hitratio'];
  window.hitratiochart.data.datasets[0].data[1] = (100 - data['hitratio']);
  window.hitratiochart.update();
  update_total_hit();

  /** Sessions chart **/
  var active_backends = data['active_backends']['nb'];
  window.sessionschart.data.datasets[0].data[0] = active_backends;
  window.sessionschart.data.datasets[0].data[1] = data['max_connections'] - active_backends;
  window.sessionschart.update();
  update_total_sessions();
}

function update_total_cpu() {
  var totalCpu = 0;
  // create a copy of data
  var data = window.cpuchart.data.datasets[0].data.slice(0);
  // last element is "idle", don't take it into account
  data.pop();
  var totalCpu = data.reduce(function(a, b) {return a + b;}, 0);
  $('#total-cpu').html(parseInt(totalCpu) + ' %');
}

function update_total_memory() {
  var totalMemory = 0;
  // create a copy of data
  var data = window.memorychart.data.datasets[0].data.slice(0);
  // last element is "Free", don't take it into account
  data.pop();
  var totalMemory = data.reduce(function(a, b) {return a + b;}, 0);
  $('#total-memory').html(parseInt(totalMemory) + ' %');
}

function update_total_hit() {
  $('#total-hit').html(window.hitratiochart.data.datasets[0].data[0] + ' %');
}

function update_total_sessions() {
  var data = window.sessionschart.data.datasets[0].data;
  var html = data[0];
  if (data[1]) {
    html += ' / ' + (data[0] + data[1]);
  }
  $('#total-sessions').html(html);
}

function resize_chart(chart, max_val, step_size_limit)
{
  while (chart.options.scales.yAxes[0].ticks.max < max_val)
  {
    chart.options.scales.yAxes[0].ticks.stepSize *= 2;
    chart.options.scales.yAxes[0].ticks.max *= 2;
  }
  while ((chart.options.scales.yAxes[0].ticks.stepSize > step_size_limit) && max_val < Math.ceil(chart.options.scales.yAxes[0].ticks.max / 2))
  {
    chart.options.scales.yAxes[0].ticks.stepSize /= 2;
    chart.options.scales.yAxes[0].ticks.max /= 2;
  }
  chart.update();
}

function updateLoadaverage(data) {
  /** Add the very new loadaverage value to the chart dataset ... **/
  var chart = window.loadaveragechart;
  chart.data.datasets[0].data.push(data['loadaverage']);
  chart.data.datasets[0].data.shift();
  $('#loadaverage').html(data['loadaverage']);
  var max = Math.max.apply(null, chart.data.datasets[0].data);
  resize_chart(window.loadaveragechart, max, 1);
}

function computeDelta(a, b, duration) {
  return Math.ceil((a - b) / duration);
}

function updateTps(data) {
  var chart = window.tpschart;
  var datasets = chart.data.datasets;
  var duration = data.timestamp - lastDatabasesDatum.timestamp;
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
  var max = Math.max.apply(null, commitData.concat(rollbackData));
  resize_chart(chart, max, 5);
  lastDatabasesDatum = data;
}

window.onload = function(){
  var options = {
    responsive : true,
    maintainAspectRatio: false,
    legend: false,
    rotation: Math.PI,
    circumference: Math.PI,
    animation: false
  };

  window.memorychart = new Chart(
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

  window.cpuchart = new Chart(
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

  window.hitratiochart = new Chart(
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

  window.sessionschart = new Chart(
    $('#chart-sessions').get(0).getContext('2d'),
    {
      type: 'doughnut',
      data: {
        labels: ["Active backends", ""],
        datasets: [
          {
            backgroundColor: ["#29cc36", "#eeeeee"]
          }
        ]
      },
      options: options
    }
  );
  update_total_sessions();

  var tpsData = jdata_history.map(function(a, index) {
    if (index === 0) {
      return [0, 0];
    }
    var curr = a.databases;
    var prev = jdata_history[index - 1].databases;
    var duration = curr.timestamp - prev.timestamp;
    var deltaCommit = computeDelta(curr.total_commit, prev.total_commit, duration);
    var deltaRollback = computeDelta(curr.total_rollback, prev.total_rollback, duration);
    return [deltaCommit, deltaRollback];
  });

  window.tpschart = new Chart(
    $('#chart-tps').get(0).getContext('2d'),
    {
      type: 'line',
      data: {
        labels: Array.apply(null, Array(jdata_history.length)),
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
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        legend: {
          display: false
        },
        scales: {
          yAxes: [{
            ticks: {
              max: 20,
              min: 0,
              stepSize: 5,
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
      }
    }
  );

  window.loadaveragechart = new Chart(
    $('#chart-loadaverage').get(0).getContext('2d'),
    {
      type: 'line',
      data: {
        labels: Array.apply(null, Array(jdata_history.length)),
        datasets : [
          {
            label: "Loadaverage",
            data: jdata_history.map(
              function(item) {
                return item.loadaverage
              }
            )
          }
        ]
      },
      options: {
        responsive : true,
        maintainAspectRatio: false,
        animation: false,
        legend: {
          display: false
        },
        scales: {
          yAxes: [{
            ticks: {
              max: 4,
              min: 0,
              stepSize: 1,
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
            backgroundColor: 'rgba(250, 164, 58, 0.2)',
            borderColor: 'rgba(250, 164, 58, 1)', //'#FAA43A'
            borderWidth: 1
          }
        },
        tooltips: {
          enabled: false
        }
      }
    }
  );

  refreshDashboard();
};

function update_notifications(data)
{
  var notif_html = '<ul class="notifications">';
  for (var i in data)
  {
    notif_html += '<li><span class="date-notification-db">'+data[i].date+'</span> <span class="badge badge-success">'+data[i].username+'</span> '+data[i].message+'</li>';
  }
  notif_html += '</ul>';
  $('#divNotif10').html(notif_html);
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
