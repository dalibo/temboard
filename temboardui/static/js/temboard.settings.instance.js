import dt from 'datatables.net-bs4';
import css from 'datatables.net-bs4/css/dataTables.bootstrap4.css';
dt(window, $);

var waitMessage = '<div class="row mb-4"><div class="col-md-4 offset-md-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>';

/*
 * Load instance properties using /json/settings/instance API
 * and build the update form.
 */
function load_update_instance_form(modal_id, agent_address, agent_port)
{
  $('#'+modal_id+'Label').html('Update instance properties');
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
      var body_html = '';
      body_html += '<form id="formUpdateInstance">';
      body_html += '  <input type="hidden" id="inputAgentAddress" value="'+data['agent_address']+'" />';
      body_html += '  <input type="hidden" id="inputAgentPort" value="'+data['agent_port']+'" />';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentAddress" class="control-label">Agent address</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentAddress" placeholder="ex: db.entreprise.lan" value="'+data['agent_address']+'" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentPort" class="control-label">Agent port</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentPort" placeholder="ex: 2345" value="'+data['agent_port']+'" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-12">';
      body_html += '      <label for="inputAgentKey" class="control-label">Agent secret key</label>';
      body_html += '      <textarea class="form-control" rows="1" id="inputAgentKey">'+data['agent_key']+'</textarea>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectGroups" class="control-label">Groups</label><br />';
      body_html += '      <select id="selectGroups" multiple="multiple">';
      var descriptions = {};
      var selected = '';
      for (var group in data['groups'])
      {
        selected = '';
        if (data['in_groups'].indexOf(group['name']) > -1)
        {
          selected = 'selected';
        }
          body_html += '      <option value="'+group['name']+'" '+selected+'>'+group['name']+'</option>';
        descriptions[group['name']] = group['description'];
      }
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectPlugins" class="control-label">Active plugins</label><br />';
      body_html += '      <select id="selectPlugins" multiple="multiple">';
      var selected = '';
      for (var plugin_name in data['loaded_plugins'])
      {
        selected = '';
        if (data['enabled_plugins'].indexOf(plugin_name) > -1)
        {
          selected = 'selected';
        }
        body_html += '      <option value="'+plugin_name+'" '+selected+'>'+plugin_name+'</option>';
      }
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="col-sm-12">';
      body_html += '      <div class="form-check">';
      body_html += '        <input type="checkbox" class="form-check-input" id="inputNotify" '+(data['notify'] ? 'checked': '')+'>';
      body_html += '        <label for="inputNotify" class="control-label">Notify users of any status alert</label>';
      body_html += '      </div>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<i class="fa fa-spinner fa-spin loader d-none"></i>';
      footer_html += '<button type="submit" id="submitFormUpdateInstance" class="btn btn-success ml-auto">Save</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';

      // Write the form.
      $('#'+modal_id+'Body').html(body_html);
      $('#'+modal_id+'Footer').html(footer_html);
      $('#submitFormUpdateInstance').click(function() {
        // Check if at least one group has been selected
        var groups = $('#selectGroups').val();
        if (groups || confirm('No group selected.\nDo you want to proceed anyway?')) {
          $('#formUpdateInstance').submit();
        }
      });
      // Activate multiselect plugin for group selecting.
      $('#selectGroups').multiselect();
      $('#selectPlugins').multiselect();
      // Add group's description as a tooltip.
      $('.multiselect-container li').not('.filter, .group').tooltip({
      placement: 'right',
      container: 'body',
      title: function () {
        var value = $(this).find('input').val();
        return descriptions[value];
        }
      });
      // Use multiselect style for Active & Admin selects.
      $('#formUpdateInstance').submit(function( event ) {
        event.preventDefault();
        updateInstance(
          modal_id,
          agent_address,
          agent_port,
          $('#inputNewAgentAddress').val(),
          $('#inputNewAgentPort').val(),
          $('#inputAgentKey').val(),
          $('#inputNotify').prop('checked')
        );
      });
    },
    error: showError.bind(null, modal_id)
  });
}

function addInstance(modal_id, address, port, key, notify) {
  var url = '/json/settings/instance';
  saveInstance(modal_id, url, address, port, key, notify);
}

function updateInstance(modal_id, address, port, newAddress, newPort, key, notify) {
  var url = ['/json/settings/instance', address, port].join('/');
  saveInstance(modal_id, url, newAddress, newPort, key, notify);
}

function saveInstance(modal_id, saveUrl, address, port, key, notify) {
  $.ajax({
    url: ['/json/discover/instance', address, port].join('/'),
    type: 'get',
    async: true,
    contentType: "application/json",
    dataType: "json",
    beforeSend: showWaiter.bind(null, modal_id),
    success: function(data) {
      $.ajax({
        url: saveUrl,
        type: 'post',
        data: JSON.stringify({
          'new_agent_address': address,
          'new_agent_port': port,
          'agent_key': $('#inputAgentKey').val(),
          'hostname': data['hostname'],
          'cpu': data['cpu'],
          'memory_size': data['memory_size'],
          'pg_data': data['pg_data'],
          'pg_port': data['pg_port'],
          'pg_version': data['pg_version'],
          'pg_version_summary': data['pg_version_summary'],
          'groups': $('#selectGroups').val(),
          'plugins': $('#selectPlugins').val(),
          'notify': notify
        }),
        async: true,
        contentType: "application/json",
        dataType: "json",
        beforeSend: showWaiter.bind(null, modal_id),
        success: function (data) {
          $('#'+modal_id).modal('hide');
          var url = window.location.href;
          window.location.replace(url);
        },
        error: showError.bind(null, modal_id)
      });
    },
    error: showError.bind(null, modal_id)
  });
}

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

/*
 *  Build the instance creation form.
 */
function load_add_instance_form(modal_id)
{
  $('#'+modal_id+'Label').html('Add a new instance');
  $.ajax({
    url: '/json/settings/all/group/instance',
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
      var body_html = '';
      body_html += '<form id="formAddInstance">';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentAddress" class="control-label">Agent address</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentAddress" placeholder="ex: db.entreprise.lan" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentPort" class="control-label">Agent port</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentPort" placeholder="ex: 2345" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-12">';
      body_html += '      <label for="inputAgentKey" class="control-label">Agent secret key</label>';
      body_html += '      <textarea class="form-control" rows="3" id="inputAgentKey"></textarea>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectGroups" class="control-label">Groups</label><br />';
      body_html += '      <select id="selectGroups" multiple="multiple">';
      var descriptions = {};
      for (var group in data['groups'])
      {
          body_html += '      <option value="'+group['name']+'">'+group['name']+'</option>';
        descriptions[group['name']] = group['description'];
      }
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectPlugins" class="control-label">Active plugins</label><br />';
      body_html += '      <select id="selectPlugins" multiple="multiple">';
      var selected = '';
      for (var plugin_name in data['loaded_plugins'])
      {
        body_html += '      <option value="'+plugin_name+'" selected>'+plugin_name+'</option>';
      }
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="col-sm-12">';
      body_html += '      <div class="form-check">';
      body_html += '        <input type="checkbox" class="form-check-input" id="inputNotify" checked>';
      body_html += '        <label for="inputNotify" class="control-label">Notify users of any status alert</label>';
      body_html += '      </div>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<i class="fa fa-spinner fa-spin loader d-none"></i>';
      footer_html += '<button type="submit" id="submitFormAddInstance" class="btn btn-success ml-auto">Save</button>';
      footer_html += '<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';

      // Write the form.
      $('#'+modal_id+'Body').html(body_html);
      $('#'+modal_id+'Footer').html(footer_html);
      $('#submitFormAddInstance').click(function() {
        $('#formAddInstance').submit()
      });
      // Activate multiselect plugin for group selecting.
      $('#selectGroups').multiselect();
      $('#selectPlugins').multiselect();
      // Add group's description as a tooltip.
      $('.multiselect-container li').not('.filter, .group').tooltip({
          placement: 'right',
          container: 'body',
          title: function () {
              var value = $(this).find('input').val();
              return descriptions[value];
          }
      });
      $('#formAddInstance').submit(function( event ) {
        event.preventDefault();
        addInstance(
          modal_id,
          $('#inputNewAgentAddress').val(),
          $('#inputNewAgentPort').val(),
          $('#inputAgentKey').val(),
          $('#inputNotify').prop('checked')
        );
      });
    },
    error: showError.bind(null, modal_id)
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

$(document).ready(function() {
  $('#tableInstances').DataTable({
    stateSave: true
  });

  $('#buttonLoadAddInstanceForm').click(function () {
    $('#InstanceModal').modal('show');
    $('[data-toggle=popover]').popover('hide');
    load_add_instance_form('InstanceModal');
  });

  $(document).on('click', '[data-action=edit]', function () {
    $('#InstanceModal').modal('show');
    $('[data-toggle=popover]').popover('hide');
    load_update_instance_form('InstanceModal', $(this).data('agent_address'), $(this).data('agent_port'));
  });

  $(document).on('click', '[data-action=delete]', function () {
    $('#InstanceModal').modal('show');
    $('[data-toggle=popover]').popover('hide');
    load_delete_instance_confirm('InstanceModal', $(this).data('agent_address'), $(this).data('agent_port'));
  });
});
