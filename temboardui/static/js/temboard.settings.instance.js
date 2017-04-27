/*
 * Load instance properties using /json/settings/instance API
 * and build the update form.
 */
function load_update_instance_form(modal_id, agent_address, agent_port)
{
  $.ajax({
    url: '/json/settings/instance/'+agent_address+'/'+agent_port,
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('');
      $('#'+modal_id+'Body').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id+'Label').html('Update instance properties');
      var body_html = '';
      body_html += '<form id="formUpdateInstance">';
      body_html += '  <input type="hidden" id="inputAgentAddress" value="'+data['agent_address']+'" />';
      body_html += '  <input type="hidden" id="inputAgentPort" value="'+data['agent_port']+'" />';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentAddress" class="control-label">Agent address</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentAddress" placeholder="db.entreprise.lan" value="'+data['agent_address']+'" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentPort" class="control-label">Agent port</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentPort" placeholder="2345" value="'+data['agent_port']+'" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-12">';
      body_html += '      <label for="inputAgentKey" class="control-label">Agent secret key</label>';
      body_html += '      <textarea class="form-control" rows="1" placeholder="Agent Secret Key" id="inputAgentKey">'+data['agent_key']+'</textarea>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectGroups" class="control-label">Groups</label><br />';
      body_html += '      <select id="selectGroups" multiple="multiple">';
      var descriptions = {};
      var selected = '';
      for (var group of data['groups'])
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
      for (var plugin_name of data['loaded_plugins'])
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
      body_html += '    <div class="form-group">';
      body_html += '      <div class="col-sm-12 text-center">';
      body_html += '        <button type="button" id="buttonDiscover" class="btn btn-default">';
      body_html += '        <i class="fa fa-download"></i>';
      body_html += '        Get instance\'s information</button>';
      body_html += '      </div>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row"><br />';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputCpu" class="control-label">Number of CPU</label><br />';
      body_html += '      <input type="text" class="form-control input-sm" id="inputCpu" placeholder="Number of CPU" value="'+null2void(data['cpu'])+'">';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputMemorySize" class="control-label">Memory size (bytes)</label><br />';
      body_html += '      <input type="text" class="form-control input-sm" id="inputMemorySize" placeholder="Memory size (byte)" value="'+null2void(data['memory_size'])+'">';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputHostname" class="control-label">Hostname</label><br />';
      body_html += '      <input type="text" class="form-control input-sm" id="inputHostname" placeholder="Hostname" value="'+data['hostname']+'">';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPgData" class="control-label">PostgreSQL data directory</label><br />';
      body_html += '      <input type="text" class="form-control input-sm" id="inputPgData" placeholder="PostgreSQL data directory" value="'+data['pg_data']+'">';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPgPort" class="control-label">PostgreSQL port</label><br />';
      body_html += '      <input type="text" class="form-control input-sm" id="inputPgPort" placeholder="PostgreSQL port" value="'+null2void(data['pg_port'])+'">';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPgVersion" class="control-label">PostgreSQL version</label><br />';
      body_html += '      <input type="text" class="form-control input-sm" id="inputPgVersion" placeholder="PostgreSQL version" value="'+data['pg_version']+'">';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<button type="submit" id="submitFormUpdateInstance" class="btn btn-success">Save</button>';
      footer_html += ' <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>';

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
        send_update_instance_form(modal_id, agent_address, agent_port);
      });
      $('#buttonDiscover').click(function(){
        $.ajax({
          url: '/json/discover/instance/'+$('#inputNewAgentAddress').val()+'/'+$('#inputNewAgentPort').val(),
          type: 'get',
          beforeSend: function(xhr){
            $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
          },
          async: true,
          contentType: "application/json",
          dataType: "json",
          success: function (data) {
            $('#inputCpu').val(data['cpu']);
            $('#inputMemorySize').val(data['memory_size']);
            $('#inputHostname').val(data['hostname']);
            $('#inputPgData').val(data['pg_data']);
            $('#inputPgVersion').val(data['pg_version']);
            $('#inputPgPort').val(data['pg_port']);
            $('#'+modal_id+'Label').html('Update instance properties');
          },
          error: function(xhr) {
            $('#'+modal_id+'Label').html('Update instance properties');
            $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
          }
        });
      });
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Update instance properties');
      $('#'+modal_id+'Body').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
    }
  });
}

function send_update_instance_form(modal_id, agent_address, agent_port)
{
  $.ajax({
    url: '/json/settings/instance/'+agent_address+'/'+agent_port,
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
    },
    data: JSON.stringify({
      'new_agent_address': $('#inputNewAgentAddress').val(),
      'new_agent_port': $('#inputNewAgentPort').val(),
      'agent_key': $('#inputAgentKey').val(),
      'hostname': $('#inputHostname').val(),
      'cpu': $('#inputCpu').val(),
      'memory_size': $('#inputMemorySize').val(),
      'pg_data': $('#inputPgData').val(),
      'pg_port': $('#inputPgPort').val(),
      'pg_version': $('#inputPgVersion').val(),
      'groups': $('#selectGroups').val(),
      'plugins': $('#selectPlugins').val()
      }),
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Update instance properties');
      $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
    }
  });
}

function load_delete_instance_confirm(modal_id, agent_address, agent_port)
{
  $.ajax({
    url: '/json/settings/instance/'+agent_address+'/'+agent_port,
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      var footer_html = '';
      footer_html += '<button type="submit" id="buttonDeleteInstance" class="btn btn-danger">Yes, delete this instance</button>';
      footer_html += ' <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>';
      $('#'+modal_id+'Label').html('Delete instance confirmation');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html(footer_html);

      $('#buttonDeleteInstance').click(function( event ) {
          event.preventDefault();
        send_delete_instance(modal_id, data['agent_address'], data['agent_port']);
      });
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Delete instance confirmation');
      $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>');
    }
  });
}

function send_delete_instance(modal_id, agent_address, agent_port)
{
  $.ajax({
    url: '/json/settings/delete/instance',
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
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
      $('#'+modal_id+'Label').html('Delete instance confirmation');
      $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
      $('#'+modal_id+'Body').html('');
    }
  });
}

/*
 *  Build the instance creation form.
 */
function load_add_instance_form(modal_id)
{
  $.ajax({
    url: '/json/settings/all/group/instance',
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('');
      $('#'+modal_id+'Body').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id+'Label').html('Add a new instance');
      $('#'+modal_id+'Info').html('');
      var body_html = '';
      body_html += '<form id="formAddInstance">';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentAddress" class="control-label">Agent address</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentAddress" placeholder="db.entreprise.lan" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewAgentPort" class="control-label">Agent port</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewAgentPort" placeholder="2345" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-12">';
      body_html += '      <label for="inputAgentKey" class="control-label">Agent secret key</label>';
      body_html += '      <textarea class="form-control" rows="3" placeholder="Agent Secret Key" id="inputAgentKey"></textarea>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectGroups" class="control-label">Groups</label><br />';
      body_html += '      <select id="selectGroups" multiple="multiple">';
      var descriptions = {};
      for (var group of data['groups'])
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
      for (var plugin_name of data['loaded_plugins'])
      {
        body_html += '      <option value="'+plugin_name+'" selected>'+plugin_name+'</option>';
      }
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="col-sm-12 text-center">';
      body_html += '      <button type="button" id="buttonDiscover" class="btn btn-success">Get instance\'s informations</button>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row"><br />';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputCpu" class="control-label">Number of CPU</label>';
      body_html += '      <input type="text" class="form-control input-sm" id="inputCpu" placeholder="Number of CPU" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputMemorySize" class="control-label">Memory size (bytes)</label>';
      body_html += '      <input type="text" class="form-control input-sm" id="inputMemorySize" placeholder="Memory size (byte)" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputHostname" class="control-label">Hostname</label>';
      body_html += '      <input type="text" class="form-control input-sm" id="inputHostname" placeholder="Hostname" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPgData" class="control-label">PostgreSQL data directory</label>';
      body_html += '      <input type="text" class="form-control input-sm" id="inputPgData" placeholder="PostgreSQL data directory" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPgPort" class="control-label">PostgreSQL port</label>';
      body_html += '      <input type="text" class="form-control input-sm" id="inputPgPort" placeholder="PostgreSQL port" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPgVersion" class="control-label">PostgreSQL version</label>';
      body_html += '      <input type="text" class="form-control input-sm" id="inputPgVersion" placeholder="PostgreSQL version" />';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<button type="submit" id="submitFormAddInstance" class="btn btn-success">Save</button>';
      footer_html += ' <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>';

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
        send_add_instance_form(modal_id);
      });
      $('#buttonDiscover').click(function(){
        $.ajax({
          url: '/json/discover/instance/'+$('#inputNewAgentAddress').val()+'/'+$('#inputNewAgentPort').val(),
          type: 'get',
          beforeSend: function(xhr){
            $('#'+modal_id+'Label').html('Processing, please wait...');
            $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
          },
          async: true,
          contentType: "application/json",
          dataType: "json",
          success: function (data) {
            $('#inputCpu').val(data['cpu']);
            $('#inputMemorySize').val(data['memory_size']);
            $('#inputHostname').val(data['hostname']);
            $('#inputPgData').val(data['pg_data']);
            $('#inputPgVersion').val(data['pg_version']);
            $('#inputPgPort').val(data['pg_port']);
            $('#'+modal_id+'Label').html('Add a new instance');
            $('#'+modal_id+'Info').html('');
          },
          error: function(xhr) {
            $('#'+modal_id+'Label').html('Add a new instance');
            $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
          }
        });
      });
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Add a new instance');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
    }
  });
}

function send_add_instance_form(modal_id)
{
  $.ajax({
    url: '/json/settings/instance',
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
    },
    data: JSON.stringify({
      'new_agent_address': $('#inputNewAgentAddress').val(),
      'new_agent_port': $('#inputNewAgentPort').val(),
      'agent_key': $('#inputAgentKey').val(),
      'hostname': $('#inputHostname').val(),
      'cpu': $('#inputCpu').val(),
      'memory_size': $('#inputMemorySize').val(),
      'pg_data': $('#inputPgData').val(),
      'pg_port': $('#inputPgPort').val(),
      'pg_version': $('#inputPgVersion').val(),
      'plugins': $('#selectPlugins').val(),
      'groups': $('#selectGroups').val()}),
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Add a new instance');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
    }
  });
}

function null2void(v){return ((v==null)?'':v);}

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
