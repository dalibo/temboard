function html_error_modal(code, error)
{
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
 * Call activity API and update the query list on success through
 * update_activity() callback.
 */
function refresh_activity(agent_address, agent_port, xsession, mode)
{
  var url_end = '';
  if (mode == 'waiting' || mode == 'blocking')
    url_end = '/'+mode;
  $.ajax({
    url: '/proxy/'+agent_address+'/'+agent_port+'/activity'+url_end,
    type: 'GET',
    beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
    async: true,
    contentType: "application/json",
    success: function (data) {
      $('#ErrorModal').modal('hide');
      switch (mode) {
        case "waiting":
        case "blocking":
          update_activity_w_b(data['rows']);
          break;
        default:
          update_activity(data['rows']);
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

var poll_activity = true;

function update_activity(data)
{
  if (!poll_activity)
  {
    return;
  }
  $("#tableActivity").html('<tr><th class="xs"></th><th class="sm">PID</th><th class="med">Database</th><th class="med">User</th><th class="sm">%CPU</th><th class="sm">%mem</th><th class="med">Read/s</th><th class="med">Write/s</th><th class="xs">IOW</th><th class="xs">W</th><th class="lg">State</th><th class="med">Duration (s)</th><th class="query">Query</th></tr>');
  for (var i = 0; i < data.length; ++i)
  {
    var class_iow = 'label-success';
    var class_wait = 'label-success';
    var class_state = '';
    if (data[i].iow == 'Y')
    {
      class_iow = 'label-danger';
    }
    if (data[i].wait == 'Y')
    {
      class_wait = 'label-danger';
    }
    switch(data[i]['state'])
    {
      case 'active':
        class_state = 'label-success';
        break;
      case 'idle in transaction':
      case 'idle in transaction (aborted)':
        class_state = 'label-danger';
        break;
      default:
        class_state = 'label-default';
    }
    var class_duration = 'none';
    if (data[i].duration > 1)
    {
      var class_duration = 'warning';
    }
    if (data[i].duration > 5)
    {
      var class_duration = 'danger';
    }
    var activity_html = '';
    activity_html += '<tr class="'+class_duration+'">';
    activity_html += '  <td><input type="checkbox" class="invisible input-xs" data-pid="'+data[i].pid+'"/></td>';
    activity_html += '  <td>'+data[i].pid+'</td>';
    activity_html += '  <td class="text-center">'+data[i].database+'</td>';
    activity_html += '  <td class="text-center">'+data[i].user+'</td>';
    activity_html += '  <td class="text-right">'+data[i].cpu+'</td>';
    activity_html += '  <td class="text-right">'+data[i].memory+'</td>';
    activity_html += '  <td class="text-right">'+data[i].read_s+'</td>';
    activity_html += '  <td class="text-right">'+data[i].write_s+'</td>';
    activity_html += '  <td><span class="label '+class_iow+'">'+data[i].iow+'</span></td>';
    activity_html += '  <td><span class="label '+class_wait+'">'+data[i].wait+'</span></td>';
    activity_html += '  <td class="text-center"><span class="label '+class_state+'">'+data[i].state+'</span></td>';
    activity_html += '  <td class="text-right">'+data[i].duration+'</td>';
    activity_html += '  <td class="query">'+escapeHtml(data[i].query)+'</td>';
    activity_html += '</tr>';
    $("#tableActivity").append(activity_html);
  }
}

function update_activity_w_b(data)
{
  if (!poll_activity)
  {
    return;
  }
  $("#tableActivity").html('<tr><th class="xs"></th><th class="sm">PID</th><th class="med">Database</th><th class="med">User</th><th class="sm">%CPU</th><th class="sm">%mem</th><th class="med">Read/s</th><th class="med">Write/s</th><th class="xs">IOW</th><th class="med">Lock Rel.</th><th class="med">Lock Mode</th><th class="med">Lock Type</th><th class="lg">State</th><th class="med">Duration (s)</th><th class="query">Query</th></tr>');
  for (var i = 0; i < data.length; ++i)
  {
    var class_iow = 'label-success';
    var class_wait = 'label-success';
    var class_state = '';
    if (data[i].iow == 'Y')
    {
      class_iow = 'label-danger';
    }
    if (data[i].wait == 'Y')
    {
      class_wait = 'label-danger';
    }
    switch(data[i]['state'])
    {
      case 'active':
        class_state = 'label-success';
        break;
      case 'idle in transaction':
      case 'idle in transaction (aborted)':
        class_state = 'label-danger';
        break;
      default:
        class_state = 'label-default';
    }
    var class_duration = 'none';
    if (data[i].duration > 1)
    {
      var class_duration = 'warning';
    }
    if (data[i].duration > 5)
    {
      var class_duration = 'danger';
    }
    var activity_html = '';
    activity_html += '<tr class="'+class_duration+'">';
    activity_html += '  <td><input type="checkbox" class="invisible input-xs" data-pid="'+data[i].pid+'"/></td>';
    activity_html += '  <td>'+data[i].pid+'</td>';
    activity_html += '  <td class="text-center">'+data[i].database+'</td>';
    activity_html += '  <td class="text-center">'+data[i].user+'</td>';
    activity_html += '  <td class="text-right">'+data[i].cpu+'</td>';
    activity_html += '  <td class="text-right">'+data[i].memory+'</td>';
    activity_html += '  <td class="text-right">'+data[i].read_s+'</td>';
    activity_html += '  <td class="text-right">'+data[i].write_s+'</td>';
    activity_html += '  <td><span class="label '+class_iow+'">'+data[i].iow+'</span></td>';
    activity_html += '  <td>'+data[i].relation+'</td>';
    activity_html += '  <td>'+data[i].mode+'</td>';
    activity_html += '  <td>'+data[i].type+'</td>';
    activity_html += '  <td class="text-center"><span class="label '+class_state+'">'+data[i].state+'</span></td>';
    activity_html += '  <td class="text-right">'+data[i].duration+'</td>';
    activity_html += '  <td class="query">'+escapeHtml(data[i].query)+'</td>';
    activity_html += '</tr>';
    $("#tableActivity").append(activity_html);
  }
}

function pause_activity()
{
  poll_activity = false;
  $('#pauseButton').addClass('hide');
  $('#resumeButton').removeClass('hide');
  $('input[type=checkbox]').each(function () {
    $(this).removeClass('invisible');
  });
  $('#loadingIndicator').addClass('hidden');
}

function resume_activity()
{
  poll_activity = true;
  $('#pauseButton').removeClass('hide');
  $('#resumeButton').addClass('hide');
  $('input:checked').each(function () {
    $(this).attr('checked', false);
  });
  $('input[type=checkbox]').each(function () {
    $(this).addClass('invisible');
  });
  $('#killButton').addClass('hide');
  $('#loadingIndicator').removeClass('hidden');
}

// show the kill button only when backends have been selected
$(document.body).on('click', 'input[type=checkbox]', function() {
  $('#killButton').toggleClass('hide', $('input:checked').length == 0);
});
function show_modal_kill(agent_address, agent_port, xsession)
{
  var pids = [];
  $('input:checked').each(function () {
    pids.push($(this).data('pid'));
  })
  if (pids.length == 0)
  {
    return;
  }
  $('#Modal').modal('show');
  $('#ModalLabel').html('Terminate backend');
  var pids_html = '';
  for(var i = 0; i < pids.length; i++)
  {
    pids_html += '<span class="label label-primary">'+pids[i]+'</span> ';
  }
  $('#ModalInfo').html(pids_html);
  var footer_html = '';
  footer_html += '<button type="button" id="submitKill" class="btn btn-danger">Yes, terminate</button>';
  footer_html += ' <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>';
  $('#ModalFooter').html(footer_html);
  $('#submitKill').click(function(){
    $.ajax({
      url: '/proxy/'+agent_address+'/'+agent_port+'/activity/kill',
      type: 'POST',
      beforeSend: function(xhr){
        xhr.setRequestHeader('X-Session', xsession);
        $('#ModalInfo').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      },
      async: true,
      contentType: "application/json",
      dataType: "json",
      data: JSON.stringify({'pids': pids}),
      success: function (data) {
        $('#Modal').modal('hide');
        var url = window.location.href;
        window.location.replace(url);
      },
      error: function(xhr) {
        if (xhr.status == 401)
        {
          $('#ModalInfo').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">Error: Session expired.</div></div></div>');
          var footer_html = '';
          footer_html += '<button type="button" id="buttonBackLogin" class="btn btn-success">Back to login page</button>';
          footer_html += ' <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>';
          $('#ModalFooter').html(footer_html);
          $('#buttonBackLogin').attr('href', '/server/'+agent_address+'/'+agent_port+'/login');
        }
        else
        {
          $('#ModalInfo').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">Error: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
          $('#ModalFooter').html('<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>');
        }
      }
    });
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
