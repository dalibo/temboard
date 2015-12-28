/*
 * Agent proxy API calls in modal box confirmation context.
 */
function modal_api_call(api_host, api_port, api_url, api_method, xsession, modal_id, json_params)
{
	$.ajax({ 
		url: '/proxy/'+api_host+'/'+api_port+api_url,
		type: api_method,
		data: JSON.stringify(json_params),
		beforeSend: function(xhr){
			$('#'+modal_id+'Label').html('Processing, please wait...');
			$('#'+modal_id+'Body').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped active" style="width: 100%;">Please wait ...</div></div></div></div>');
			$('#'+modal_id+'Footer').html('<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>');
			xhr.setRequestHeader('X-Session', xsession);
		},
		async: true,
		contentType: "application/json",
		dataType: "json",
		success: function (data) {
			var url = window.location.href;
			window.location.replace(url);
		},
		error: function(xhr) {
			if (xhr.status == 401)
			{
				$('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">Session expired. <a class="btn btn-danger" id="ConfirmOK" href="/server/'+ghost+'/'+gport+'/login">Back to login page</a></div>');
			}
			else
			{
				$('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div>');
			}
		}
	});
}
