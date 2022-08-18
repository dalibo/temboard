var waitMessage = '<div class="row mb-4"><div class="col-md-4 offset-md-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>';

function showError(modal_id, xhr) {
  hideWaiter(modal_id);
  $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
}

function showWaiter(modal_id) {
  $('#' + modal_id + ' .test-check-ok').addClass('d-none');
  $('#' + modal_id + 'Info').html('');
  $('#' + modal_id + ' .loader').removeClass('d-none');
}

function hideWaiter(modal_id) {
  $('#' + modal_id + ' .loader').addClass('d-none');
}

function load_delete_instance_confirm(modal_id, agent_address, agent_port)
{
  $('#'+modal_id+'Label').html('Delete instance confirmation');
  $.ajax({
    url: '/json/settings/instance/'+agent_address+'/'+agent_port,
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Info').html(waitMessage);
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id+'Info').html('');
      var footer_html = '';
      footer_html += '<button type="submit" id="buttonDeleteInstance" class="btn btn-danger">Yes, delete this instance</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html(footer_html);

      $('#buttonDeleteInstance').click(function( event ) {
          event.preventDefault();
        send_delete_instance(modal_id, data['agent_address'], data['agent_port']);
      });
    },
    error: function(xhr) {
      showError(modal_id, xhr);
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    }
  });
}

function send_delete_instance(modal_id, agent_address, agent_port)
{
  $.ajax({
    url: '/json/settings/delete/instance',
    type: 'post',
    beforeSend: function(xhr){
      showWaiter(modal_id);
      $('#'+modal_id+'Body').html('');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({ 'agent_address': agent_address, 'agent_port': agent_port }),
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      showError(xhr, modal_id);
      $('#'+modal_id+'Body').html('');
    }
  });
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
