/*
 * Call ganeshd /administration/control API and update the dashboard on success through
 * update_dashboard() callback.
 */
function administration_control(ghost, gport, xsession, req_action)
{
	var key = 'action';
	var json_params = {};
	json_params[key] = req_action;
	$.ajax({ 
		url: '/proxy/'+ghost+'/'+gport+'/administration/control',
		type: 'POST',
		data: JSON.stringify(json_params),
		beforeSend: function(xhr){
			$('#restartModalLabel').html('Restarting PostgreSQL, please wait...');
			$('#restartModalBody').html('<div class="row"><div class="col-md-4"></div><div class="col-md-4"><img src="/imgs/ajax-loader.gif" /></div><div class="col-md-4"></div></div>');
			$('#restartModalFooter').html('<button type="button" class="btn btn-primary" data-dismiss="modal">Close</button>');
			xhr.setRequestHeader('X-Session', xsession);
		},
		async: true,
		contentType: "application/json",
		dataType: "json",
		
		success: function (data) {
			$('#restartModalBody').html('Done.');
			$('#restartModalFooter').html('<button type="button" class="btn btn-primary" id="restartClose">Close</button><script>$("#restartClose").click(function(){var url = window.location.href;window.location.replace(url);});</script>');
		},
		error: function(xhr) {
			if (xhr.status == 401)
			{
				$('#restartModalBody').html('<div class="alert alert-danger" role="alert">Session expired. <a class="btn btn-danger" id="ConfirmOK" href="/server/'+ghost+'/'+gport+'/login">Back to login page</a></div>');
			}
			else
			{
				$('#restartModalBody').html('<div class="alert alert-danger" role="alert">ERROR '+xhr.status+':'+JSON.parse(xhr.responseText).error+'</div>');
			}
		}
	});
}


