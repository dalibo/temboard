var last_update_timestamp = 0;

// Chart.js 2.X plugin to force display of tooltips with doughnut charts.
Chart.pluginService.register({
  beforeRender: function (chart) {
    if (chart.config.options.showAllTooltips) {
      // create an array of tooltips
      // we can't use the chart tooltip because there is only one tooltip per chart
      chart.pluginTooltips = [];
      chart.config.data.datasets.forEach(function (dataset, i) {
        chart.getDatasetMeta(i).data.forEach(function (sector, j) {
          chart.pluginTooltips.push(new Chart.Tooltip({
            _chart: chart.chart,
            _chartInstance: chart,
            _data: chart.data,
            _options: chart.options.tooltips,
            _active: [sector]
          }, chart));
        });
      });

      // turn off normal tooltips
      chart.options.tooltips.enabled = false;
    }
  },
  afterDraw: function (chart, easing) {
    if (chart.config.options.showAllTooltips) {
      // we don't want the permanent tooltips to animate, so don't do anything till the animation runs atleast once
      if (!chart.allTooltipsOnce) {
        if (easing !== 1) {
          return;
        }
        chart.allTooltipsOnce = true;
      }

      // turn on tooltips
      chart.options.tooltips.enabled = true;
      Chart.helpers.each(chart.pluginTooltips, function (tooltip) {
        tooltip.initialize();
        tooltip.update();
        // we don't actually need this since we are not animating tooltips
        tooltip.pivot();
        tooltip.transition(easing).draw();
      });
      chart.options.tooltips.enabled = false;
    }
  }
});

/*
 * CPU & Memory usage donut charts options.
 */
var options = {
  responsive : true,
  maintainAspectRatio: false,
  showAllTooltips: true,
  legend: {
    display: false
  },
  animation: {
    duration: 0
  },
  tooltips: {
    callbacks: {
      label: function(tooltipItem, data) {
        return data.labels[tooltipItem.index]+': '+data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index] + ' %';
      }
    }
  }
};

function html_error_modal(code, error) {
  var error_html = '';
  error_html += '<div class="modal" id="ErrorModal" tabindex="-1" role="dialog" aria-labelledby="ErrorModalLabel" aria-hidden="true">';
  error_html += '   <div class="modal-dialog">';
  error_html += '     <div class="modal-content">';
  error_html += '       <div class="modal-header">';
  error_html += '         <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
  error_html += '         <h4 class="modal-title" id="ErrorModalLabel">Error '+code+'</h4>';
  error_html += '       </div>';
  error_html += '       <div class="modal-body">';
  error_html += '         <div class="alert alert-danger" role="alert">'+error+'</div>';
  error_html += '       </div>';
  error_html += '       <div class="modal-footer" id="ErrorModalFooter">';
  error_html += '         <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>';
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
function refresh_dashboard(agent_address, agent_port, xsession)
{
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
        update_tps(data, true);
        update_loadaverage(data, true);
        update_buffers(data, true);
        update_backends(data, true);
        update_notifications(data.notifications);
      }
    },
    error: function(xhr) {
      if (xhr.status == 401)
      {
        $('#ErrorModal').modal('hide');
        $('#modalError').html(html_error_modal(401, 'Session expired'));
        $('#ErrorModalFooter').html('<a class="btn btn-default" id="aBackLogin">Back to login page</a>');
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
  /** Update CPU usage chart **/
  window.cpuchart.data.datasets[0].data[0] = data['cpu']['iowait'];
  window.cpuchart.data.datasets[0].data[1] = data['cpu']['steal'];
  window.cpuchart.data.datasets[0].data[2] = data['cpu']['user'];
  window.cpuchart.data.datasets[0].data[3] = data['cpu']['system'];
  window.cpuchart.data.datasets[0].data[4] = data['cpu']['idle'];
  window.cpuchart.update();
  /** Hitratio chart **/
  window.hitratiochart.data.datasets[0].data[0] = data['hitratio'];
  window.hitratiochart.data.datasets[0].data[1] = (100 - data['hitratio']);
  window.hitratiochart.update();
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

/*
 * Loadaverage line chart options.
 */
var loadaverage_config = {
  type: 'line',
  data: {
    labels: [ "","","","","","","","","","","","","","","","","","","","" ],
    datasets : [
      {
        label: "Loadaverage",
        data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
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
        radius: 0
      },
      line: {
        backgroundColor: 'rgba(101,152,184,0.2)',
        borderColor: "rgba(101,152,184,1)",
        borderWidth: 1
      }
    },
    tooltips: {
      enabled: false
    }
  }
};

var loadaverage_values = [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null];

function update_loadaverage(data, update_chart)
{
  if (!("loadaveragechart" in window))
  {
    var loadaveragecontext = $('#chart-loadaverage').get(0).getContext('2d');
    window.loadaveragechart = new Chart(loadaveragecontext, loadaverage_config);
  }
  /** Add the very new loadaverage value to the chart dataset ... **/
  window.loadaveragechart.data.datasets[0].data.push(data['loadaverage']);
  /** ... and to the global array loadaverage_values **/
  loadaverage_values.push(data['loadaverage']);
  loadaverage_values.shift();
  window.loadaveragechart.data.datasets[0].data.shift();
  if (update_chart)
  {
    $('#loadaverage').html(data['loadaverage']);
    var max_val = 0;
    var i = 0;
    for (i; i < loadaverage_values.length; i++)
    {
      if (loadaverage_values[i] > max_val)
      {
        max_val = loadaverage_values[i];
      }
    }
    resize_chart(window.loadaveragechart, max_val, 1);
  }
}

/*
 * Buffers line chart options.
 */
var buffers_config = {
  type: 'line',
  data: {
    labels: [ "","","","","","","","","","","","","","","","","","","","" ],
    datasets : [
      {
        label: "Buffers",
        data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
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
        radius: 0
      },
      line: {
        backgroundColor: 'rgba(101,152,184,0.2)',
        borderColor: "rgba(101,152,184,1)",
        borderWidth: 1
      }
    },
    tooltips: {
      enabled: false
    }
  }
};
var buffers_values = [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null];

function update_buffers(data, update_chart)
{
  if (!("bufferschart" in window))
  {
    var bufferscontext = $('#chart-buffers').get(0).getContext('2d');
    window.bufferschart = new Chart(bufferscontext, buffers_config);
  }
  /** Re-process delta calculation **/
  if (buffers_values.length > 0)
  {
    var p = buffers_values.length - 1;
    if (buffers_values[p] != null)
    {
      delta = data['buffers']['nb'] - buffers_values[p]['nb'];
    } else {
      delta = 0;
    }
  } else {
    delta = 0;
  }

  window.bufferschart.data.datasets[0].data.push(delta);
  /** We need to store delta value. **/
  data['buffers']['delta'] = delta;
  buffers_values.push(data['buffers']);
  window.bufferschart.data.datasets[0].data.shift();
  buffers_values.shift();
  if (update_chart)
  {
    $('#buffers_delta').html(delta);
    var max_val = 0;
    for (var i=0; i < buffers_values.length; i++)
    {
      if (buffers_values[i] != null && buffers_values[i]['delta'] > max_val)
      {
        max_val = buffers_values[i]['delta'];
      }
    }
    resize_chart(window.bufferschart, max_val, 5);
  }
}

/*
 * Active Backends line chart options.
 */
var backends_config = {
  type: 'line',
  data: {
    labels: [ "","","","","","","","","","","","","","","","","","","","" ],
    datasets : [
      {
        label: "Active Backends",
        data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
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
        radius: 0
      },
      line: {
        backgroundColor: 'rgba(101,152,184,0.2)',
        borderColor: 'rgba(101,152,184,1)',
        borderWidth: 1
      }
    },
    tooltips: {
      enabled: false
    }
  }
};


var backends_values = [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null];

function update_backends(data, update_chart)
{
  if (!("backendschart" in window))
  {
    var backends_context = $('#chart-backends').get(0).getContext('2d');
    window.backendschart = new Chart(backends_context, backends_config);
  }
  /** Add the very new backends value to the chart dataset ... **/
  window.backendschart.data.datasets[0].data.push(data['active_backends']['nb']);
  /** ... and to the global array backends_values **/
  backends_values.push(data['active_backends']['nb']);
  window.backendschart.data.datasets[0].data.shift();
  backends_values.shift();
  if (update_chart)
  {
    $('#backends').html(data['active_backends']['nb']);
    var max_val = 0;
    for (var i=0; i < backends_values.length; i++)
    {
      if (backends_values[i] > max_val)
      {
        max_val = backends_values[i];
      }
    }
    resize_chart(window.backendschart, max_val, 1);
  }
}

/*
 * TPS line chart options.
 */

var tps_config = {
  type: 'line',
  data: {
    labels: [ "","","","","","","","","","","","","","","","","","","","" ],
    datasets : [
      {
        label: "Commit",
        backgroundColor: "rgba(0,188,18,0.2)",
        borderColor: "rgba(0,188,18,1)",
        data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
      },
      {
        label: "Rollback",
        backgroundColor: "rgba(188,0,0,0.2)",
        borderColor: "rgba(188,0,0,1)",
        data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
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
        radius: 0
      },
      line: {
        borderWidth: 1
      }
    },
    tooltips: {
      enabled: false
    }
  }
};

var tps_values = [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null];

function update_tps(data, update_chart)
{
  if (!("tpschart" in window))
  {
    var tps_context = $('#chart-tps').get(0).getContext('2d');
    window.tpschart = new Chart(tps_context, tps_config);
  }
  /** Proceed with delta calculation **/
  if (tps_values.length > 0)
  {
    var p = tps_values.length - 1;
    if (tps_values[p] != null)
    {
      delta_commit = Math.ceil((data['databases']['total_commit'] - tps_values[p]['total_commit']) / (data['databases']['timestamp'] - tps_values[p]['timestamp']));
      delta_rollback = Math.ceil((data['databases']['total_rollback'] - tps_values[p]['total_rollback']) / (data['databases']['timestamp'] - tps_values[p]['timestamp']));
    } else {
      delta_commit = 0;
      delta_rollback = 0;
    }
  } else {
    delta_commit = 0;
    delta_rollback = 0;
  }

  window.tpschart.data.datasets[0].data.push(delta_commit);
  window.tpschart.data.datasets[1].data.push(delta_rollback);
  /** We need to store delta value. **/
  data['databases']['delta_commit'] = delta_commit;
  data['databases']['delta_rollback'] = delta_rollback;
  tps_values.push(data['databases']);
  tps_values.shift();
  window.tpschart.data.datasets[0].data.shift();
  window.tpschart.data.datasets[1].data.shift();
  if (update_chart)
  {
    $('#tps_commit').html(delta_commit);
    $('#tps_rollback').html(delta_rollback);
    var max_val = 0;
    for (var i=0; i < tps_values.length; i++)
    {
      if (tps_values[i] != null)
      {
        if (tps_values[i]['delta_commit'] > max_val)
        {
          max_val = tps_values[i]['delta_commit'];
        }
        if (tps_values[i]['delta_rollback'] > max_val)
        {
          max_val = tps_values[i]['delta_rollback'];
        }
      }
    }
    resize_chart(window.tpschart, max_val, 5);
  }
}

window.onload = function(){
  var memorycontext = $('#chart-memory').get(0).getContext('2d');
  window.memorychart = new Chart(memorycontext, {type: 'doughnut', data: memorydata, options: options});
  var cpucontext = $('#chart-cpu').get(0).getContext('2d');
  window.cpuchart = new Chart(cpucontext, {type: 'doughnut', data: cpudata, options: options});
  var hitratiocontext = $('#chart-hitratio').get(0).getContext('2d');
  window.hitratiochart = new Chart(hitratiocontext, {type: 'doughnut', data: hitratiodata, options: options});
};

function update_notifications(data)
{
  var notif_html = '<ul class="notifications">';
  for (var i in data)
  {
    notif_html += '<li><span class="date-notification-db">'+data[i].date+'</span> <span class="label label-success">'+data[i].username+'</span> '+data[i].message+'</li>';
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
