/*
 * Call ganeshd /activity API and update the query list on success through
 * update_activity() callback.
 */
function refresh_activity(ghost, gport, xsession)
{
	$.ajax({ 
		url: '/proxy/'+ghost+'/'+gport+'/activity',
		type: 'GET',
		beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
		async: true,
		contentType: "application/json",
		success: function (data) {
			update_activity(data['rows']);
		},
		error: function(xhr) {
			if (xhr.status == 401)
			{
				$('#myModal').modal('hide');
				$('#modalError').html('<div class="modal" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><h4 class="modal-title" id="myModalLabel">ERROR</h4></div><div class="modal-body"><div class="alert alert-danger" role="alert">Session expired.</div></div><div class="modal-footer"><a class="btn btn-primary" id="ConfirmOK">Back to login page</a></div></div></div></div>');
				$('#ConfirmOK').attr('href', '/server/'+ghost+'/'+gport+'/login');
				$('#myModal').modal({show:true});
			}
			else
			{
				$('#myModal').modal('hide');
				$('#modalError').html('<div class="modal" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><h4 class="modal-title" id="myModalLabel">ERROR '+xhr.status+'</h4></div><div class="modal-body"><div class="alert alert-danger" role="alert">'+JSON.parse(xhr.responseText).error+'</div></div><div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Close</button></div></div></div></div>');
				$('#myModal').modal({show:true});
			}
		}
	});
}

var $poll_activity = true;

function update_activity(data)
{
	if (!$poll_activity)
	{
		return;
	}
	$("#tableActivity").html('<tr><th class="xs"></th><th class="sm">PID</th><th class="med">Database</th><th class="med">User</th><th class="sm">%CPU</th><th class="sm">%mem</th><th class="med">Read/s</th><th class="med">Write/s</th><th class="xs">IOW</th><th class="xs">W</th><th class="med">State</th><th class="med">Duration</th><th class="query">Query</th></tr>');
	for (var i = 0; i < data.length; ++i)
	{
		var class_iow = 'no';
		var class_wait = 'no';
		if (data[i].iow == 'Y')
		{
			class_iow = 'yes';
		}
		if (data[i].wait == 'Y')
		{
			class_wait = 'yes';
		}
		$("#tableActivity").append('<tr><td><input type="checkbox" class="input-xs" /></td><td>'+data[i].pid+'</td><td>'+data[i].database+'</td><td>'+data[i].user+'</td><td class="cpu">'+data[i].cpu+'</td><td class="mem">'+data[i].memory+'</td><td class="read">'+data[i].read_s+'</td><td class="write">'+data[i].write_s+'</td><td class="'+class_iow+'">'+data[i].iow+'</td><td class="'+class_wait+'">'+data[i].wait+'</td><td>'+data[i].state+'</td><td>'+data[i].duration+'</td><td class="query">'+data[i].query+'</td></tr>');
	}
}

function pause_activity()
{
	$poll_activity = false;
	$("#pauseButton").removeClass('btn-primary').addClass('btn-warning');
}

function resume_activity()
{
	$poll_activity = true;
	$("#pauseButton").removeClass('btn-warning').addClass('btn-primary');
}
