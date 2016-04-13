/*
 * Loadaverage line chart options.
 */
var loadaverageoptions = {
	responsive : true,
	animation: false,
	scaleBeginAtZero: true,
	bezierCurve : true,
	pointDot: false,
	showTooltips: false,
	scaleShowVerticalLines: false,
	scaleIntegersOnly: true,
	scaleStartValue: 0,
	scaleOverride: true,
	scaleSteps: 4,
	scaleStepWidth: 0.5
};

/*
 * Buffers line chart options.
 */
var buffersoptions = {
	responsive : true,
	animation: false,
	scaleBeginAtZero: true,
	bezierCurve : true,
	pointDot: false,
	showTooltips: false,
	scaleShowVerticalLines: false,
	scaleIntegersOnly: true,
	scaleStartValue: 0,
	scaleOverride: true,
	scaleSteps: 4,
	scaleStepWidth: 5
};

/*
 * Active Backends line chart options.
 */
var backendsoptions = {
	responsive : true,
	animation: false,
	scaleBeginAtZero: true,
	bezierCurve : true,
	pointDot: false,
	showTooltips: false,
	scaleShowVerticalLines: false,
	scaleIntegersOnly: true,
	scaleStartValue: 0,
	scaleOverride: true,
	scaleSteps: 4,
	scaleStepWidth: 1
};

/*
 * TPS line chart options.
 */
var tpsoptions = {
	responsive : true,
	animation: false,
	scaleBeginAtZero: true,
	bezierCurve : true,
	pointDot: false,
	showTooltips: false,
	scaleShowVerticalLines: false,
	scaleIntegersOnly: true,
	scaleStartValue: 0,
	scaleOverride: true,
	scaleSteps: 4,
	scaleStepWidth: 5
};
var loadaveragedata = {
	labels: [ "","","","","","","","","","","","","","","","","","","","" ],
	datasets : [
			{
				label: "Loadaverage",
				fillColor: "rgba(101,152,184,0.2)",
				strokeColor: "rgba(101,152,184,1)",
				pointColor: "rgba(101,152,184,1)",
				pointStrokeColor: "#fff",
				pointHighlightFill: "#fff",
				pointHighlightStroke: "rgba(101,152,184,1)",
				data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
			}
	]
};
var buffersdata = {
	labels: [ "","","","","","","","","","","","","","","","","","","","" ],
	datasets : [
			{
				label: "Buffers",
				fillColor: "rgba(101,152,184,0.2)",
				strokeColor: "rgba(101,152,184,1)",
				pointColor: "rgba(101,152,184,1)",
				pointStrokeColor: "#fff",
				pointHighlightFill: "#fff",
				pointHighlightStroke: "rgba(101,152,184,1)",
				data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
			}
	]
};
var backendsdata = {
	labels: [ "","","","","","","","","","","","","","","","","","","","" ],
	datasets : [
			{
				label: "Active Backends",
				fillColor: "rgba(101,152,184,0.2)",
				strokeColor: "rgba(101,152,184,1)",
				pointColor: "rgba(101,152,184,1)",
				pointStrokeColor: "#fff",
				pointHighlightFill: "#fff",
				pointHighlightStroke: "rgba(101,152,184,1)",
				data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
			}
	]
};
var tpsdata = {
	labels: [ "","","","","","","","","","","","","","","","","","","","" ],
	datasets : [
			{
				label: "Commit",
				fillColor: "rgba(0,188,18,0.2)",
				strokeColor: "rgba(0,188,18,1)",
				pointColor: "rgba(0,188,18,1)",
				pointStrokeColor: "#fff",
				pointHighlightFill: "#fff",
				pointHighlightStroke: "rgba(0,188,18,1)",
				data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
			},
			{
				label: "Rollback",
				fillColor: "rgba(188,0,0,0.2)",
				strokeColor: "rgba(188,0,0,1)",
				pointColor: "rgba(188,0,0,1)",
				pointStrokeColor: "#fff",
				pointHighlightFill: "#fff",
				pointHighlightStroke: "rgba(188,0,0,1)",
				data: [null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]
			}
	]
};

var loadaverage_values = loadaveragedata.datasets[0].data;
var buffers_values = buffersdata.datasets[0].data;
var backends_values = backendsdata.datasets[0].data;
var tps_values = tpsdata.datasets[0].data;
var last_update_timestamp = 0;

/*
 * CPU & Memory usage donut charts options.
 */
var options = {
	tooltipTemplate: "<%= label %>: <%= value %>%",
	responsive : true,
	animation: false,
	onAnimationComplete: function()
	{
		/** Force the display of tooltips. **/
		var new_segments = [];
		var pos = 0
		for (var i=0; i <this.segments.length; i++)
		{
			if (this.segments[i].value > 0)
			{
				new_segments[pos] = this.segments[i]
				pos++
			}
		}
		this.showTooltip(new_segments, true);
	},
	tooltipEvents: [],
	showTooltips: true
}

function html_error_modal(code, error)
{
	var error_html = '';
	error_html += '<div class="modal" id="ErrorModal" tabindex="-1" role="dialog" aria-labelledby="ErrorModalLabel" aria-hidden="true">';
	error_html += '		<div class="modal-dialog">';
	error_html += '			<div class="modal-content">';
	error_html += '				<div class="modal-header">';
	error_html += '					<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
	error_html += '					<h4 class="modal-title" id="ErrorModalLabel">Error '+code+'</h4>';
	error_html += '				</div>';
	error_html += '				<div class="modal-body">';
	error_html += '					<div class="alert alert-danger" role="alert">'+error+'</div>';
	error_html += '				</div>';
	error_html += '				<div class="modal-footer" id="ErrorModalFooter">';
	error_html += '					<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>';
	error_html += '				</div>';
	error_html += '			</div>';
	error_html += '		</div>';
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
	$('#memory').html(data['memory']['total']);
	$('#pg_version').html(data['pg_version']);
	$('#size').html(data['databases']['total_size']);
	$('#nb_db').html(data['databases']['databases']);
	$('#pg_data').html(data['pg_data']);
	$('#pg_port').html(data['pg_port']);
	$('#pg_uptime').html(data['pg_uptime']);
	/** Update memory usage chart **/
	
	window.memorychart.segments[0].value = data['memory']['active'];
	window.memorychart.segments[1].value = data['memory']['cached'];
	window.memorychart.segments[2].value = data['memory']['free'];
	window.memorychart.update();
	/** Update CPU usage chart **/
	window.cpuchart.segments[0].value = data['cpu']['iowait'];
	window.cpuchart.segments[1].value = data['cpu']['steal'];
	window.cpuchart.segments[2].value = data['cpu']['user'];
	window.cpuchart.segments[3].value = data['cpu']['system'];
	window.cpuchart.segments[4].value = data['cpu']['idle'];
	window.cpuchart.update();
	/** Hitratio chart **/
	window.hitratiochart.segments[0].value = data['hitratio'];
	window.hitratiochart.segments[1].value = (100 - data['hitratio']);
	window.hitratiochart.update();
}

function update_loadaverage(data, update_chart)
{
	if (!("loadaveragechart" in window))
	{
		var loadaveragecontext = $('#chart-loadaverage').get(0).getContext('2d');
		window.loadaveragechart = new Chart(loadaveragecontext).Line(loadaveragedata, loadaverageoptions);
	}
	/** Add the very new loadaverage value to the chart dataset ... **/
	window.loadaveragechart.addData([data['loadaverage']], "");
	/** ... and to the global array loadaverage_values **/
	loadaverage_values.push(data['loadaverage']);
	window.loadaveragechart.removeData();
	loadaverage_values.shift();
	if (update_chart)
	{
		$('#loadaverage').html(data['loadaverage']);
		var max_val = 0;
		for (var i=0; i < loadaverage_values.length; i++)
		{
			if (loadaverage_values[i] > max_val)
			{
				max_val = loadaverage_values[i];
			}
		}
		while (Math.ceil(window.loadaveragechart.options.scaleSteps * window.loadaveragechart.options.scaleStepWidth) < max_val)
		{
			window.loadaveragechart.options.scaleStepWidth *= 2;
			window.loadaveragechart.buildScale(loadaveragedata.labels);
		}
		while ((window.loadaveragechart.options.scaleStepWidth > 0.5) && max_val < Math.ceil(window.loadaveragechart.options.scaleSteps * window.loadaveragechart.options.scaleStepWidth / 2))
		{
			window.loadaveragechart.options.scaleStepWidth /= 2;
			window.loadaveragechart.buildScale(loadaveragedata.labels);
		}
		window.loadaveragechart.update();
	}
}

function update_buffers(data, update_chart)
{
	if (!("bufferschart" in window))
	{
		var bufferscontext = $('#chart-buffers').get(0).getContext('2d');
		window.bufferschart = new Chart(bufferscontext).Line(buffersdata, buffersoptions);
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

	window.bufferschart.addData([delta], "");
	/** We need to store delta value. **/
	data['buffers']['delta'] = delta;
	buffers_values.push(data['buffers']);
	window.bufferschart.removeData();
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
		while (Math.ceil(window.bufferschart.options.scaleSteps * window.bufferschart.options.scaleStepWidth) < max_val)
		{
			window.bufferschart.options.scaleStepWidth *= 2;
			window.bufferschart.buildScale(buffersdata.labels);
		}
		while ((window.bufferschart.options.scaleStepWidth > 5) && max_val < Math.ceil(window.bufferschart.options.scaleSteps * window.bufferschart.options.scaleStepWidth / 2))
		{
			window.bufferschart.options.scaleStepWidth /= 2;
			window.bufferschart.buildScale(buffersdata.labels);
		}
		window.bufferschart.update();
	}
}

function update_backends(data, update_chart)
{
	if (!("backendschart" in window))
	{
		var backendscontext = $('#chart-backends').get(0).getContext('2d');
		window.backendschart = new Chart(backendscontext).Line(backendsdata, backendsoptions);
	}
	/** Add the very new backends value to the chart dataset ... **/
	window.backendschart.addData([data['active_backends']['nb']], "");
	/** ... and to the global array backends_values **/
	backends_values.push(data['active_backends']['nb']);
	window.backendschart.removeData();
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
		while (Math.ceil(window.backendschart.options.scaleSteps * window.backendschart.options.scaleStepWidth) < max_val)
		{
			window.backendschart.options.scaleStepWidth *= 2;
			window.backendschart.buildScale(backendsdata.labels);
		}
		while ((window.backendschart.options.scaleStepWidth > 1) && max_val < Math.ceil(window.backendschart.options.scaleSteps * window.backendschart.options.scaleStepWidth / 2))
		{
			window.backendschart.options.scaleStepWidth /= 2;
			window.backendschart.buildScale(backendsdata.labels);
		}
		window.backendschart.update();
	}
}

function update_tps(data, update_chart)
{
	if (!("tpschart" in window))
	{
		window.tpschart = new Chart($('#chart-tps').get(0).getContext('2d')).Line(tpsdata, tpsoptions);
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

	window.tpschart.addData([delta_commit, delta_rollback], "");
	/** We need to store delta value. **/
	data['databases']['delta_commit'] = delta_commit;
	data['databases']['delta_rollback'] = delta_rollback;
	tps_values.push(data['databases']);
	window.tpschart.removeData();
	tps_values.shift();
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
		while (Math.ceil(window.tpschart.options.scaleSteps * window.tpschart.options.scaleStepWidth) < max_val)
		{
			window.tpschart.options.scaleStepWidth *= 2;
			window.tpschart.buildScale(tpsdata.labels);
		}
		while ((window.tpschart.options.scaleStepWidth > 5) && max_val < Math.ceil(window.tpschart.options.scaleSteps * window.tpschart.options.scaleStepWidth / 2))
		{
			window.tpschart.options.scaleStepWidth /= 2;
			window.tpschart.buildScale(tpsdata.labels);
		}
		window.tpschart.update();
	}
}

window.onload = function(){
	var memorycontext = $('#chart-memory').get(0).getContext('2d');
	window.memorychart = new Chart(memorycontext).Doughnut(memorydata, options);
	var cpucontext = $('#chart-cpu').get(0).getContext('2d');
	window.cpuchart = new Chart(cpucontext).Doughnut(cpudata, options);
	var hitratiocontext = $('#chart-hitratio').get(0).getContext('2d');
	window.hitratiochart = new Chart(hitratiocontext).Doughnut(hitratiodata, options);
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
