/*
 * ganeshd API calls in modal box confirmation context.
 */
function modal_api_call(api_host, api_port, api_url, api_method, xsession, modal_id, json_params)
{
	$.ajax({ 
		url: '/proxy/'+api_host+'/'+api_port+api_url,
		type: api_method,
		data: JSON.stringify(json_params),
		beforeSend: function(xhr){
			$('#'+modal_id+'Label').html('Processing, please wait...');
			$('#'+modal_id+'Body').html('<div class="row"><div class="col-md-4"></div><div class="col-md-4"><img src="/imgs/ajax-loader.gif" /></div><div class="col-md-4"></div></div>');
			$('#'+modal_id+'Footer').html('<button type="button" class="btn btn-primary" data-dismiss="modal">Close</button>');
			xhr.setRequestHeader('X-Session', xsession);
		},
		async: true,
		contentType: "application/json",
		dataType: "json",
		
		success: function (data) {
			$('#'+modal_id+'Body').html('Done.');
			$('#'+modal_id+'Footer').html('<button type="button" class="btn btn-primary" id="'+modal_id+'Close">Close</button><script>$("#'+modal_id+'Close").click(function(){var url = window.location.href;window.location.replace(url);});</script>');
		},
		error: function(xhr) {
			if (xhr.status == 401)
			{
				$('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">Session expired. <a class="btn btn-danger" id="ConfirmOK" href="/server/'+ghost+'/'+gport+'/login">Back to login page</a></div>');
			}
			else
			{
				$('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">ERROR '+xhr.status+':'+JSON.parse(xhr.responseText).error+'</div>');
			}
		}
	});
}
