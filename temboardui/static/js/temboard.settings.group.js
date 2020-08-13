var multiselectOptions = {
  templates: {
    button: '<button type="button" class="multiselect dropdown-toggle border-secondary" data-toggle="dropdown"><span class="multiselect-selected-text"></span> <b class="caret"></b></button>',
    li: '<li class="dropdown-item"><a href="javascript:void(0);"><label></label></a></li>'
  }
};

/*
 * Load group properties using /json/settings/group/<group_kind>/<group_name> API
 * and build the update form.
 */
function load_update_group_form(modal_id, group_kind, group_name)
{
  $.ajax({
    url: '/json/settings/group/'+group_kind+'/'+group_name,
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('');
      $('#'+modal_id+'Body').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      if (data['kind'] == 'role')
      {
        $('#'+modal_id+'Label').html('Update user group properties');
      } else {
        $('#'+modal_id+'Label').html('Update instance group properties');
      }
      var body_html = '';
      body_html += '<form id="formUpdateGroup">';
      body_html += '  <input type="hidden" id="inputGroupname" value="'+data['name']+'" />';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewGroupname" class="control-label">Group name</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewGroupname" placeholder="New group name" value="'+data['name']+'" />';
      body_html += '    </div>';
      if (group_kind == 'instance')
      {
        body_html += '    <div class="form-group col-sm-6">';
        body_html += '      <label for="selectGroups" class="control-label">User groups</label><br />';
        body_html += '      <select id="selectGroups" multiple="multiple">';
        var descriptions = {};
        var selected = '';
        for (var group of data['user_groups'])
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
        body_html += '      <p class="form-text text-muted">Please select the user groups allowed to view instances from this instance group.</p>';
        body_html += '    </div>';
      }
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-12">';
      body_html += '      <label for="inputDescription" class="control-label">Description</label>';
      body_html += '      <textarea class="form-control" rows="3" placeholder="Description" id="inputDescription">'+data['description']+'</textarea>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<button type="submit" id="submitFormUpdateGroup" class="btn btn-success">Save</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
      // Write the form.
      $('#'+modal_id+'Body').html(body_html);
      $('#'+modal_id+'Footer').html(footer_html);
      if (group_kind == 'instance')
      {
        // Activate multiselect plugin for group selecting.
        $('#selectGroups').multiselect(multiselectOptions);
        // Add group's description as a tooltip.
        $('.multiselect-container li').not('.filter, .group').tooltip({
            placement: 'right',
            container: 'body',
            title: function () {
                var value = $(this).find('input').val();
                return descriptions[value];
            }
        });
      }
      $('#submitFormUpdateGroup').click(function() {
        $('#formUpdateGroup').submit()
      });
      $('#formUpdateGroup').submit(function( event ) {
          event.preventDefault();
        send_update_group_form(modal_id, data['kind']);
      });
    },
    error: function(xhr) {
      if (group_kind == 'role')
      {
        $('#'+modal_id+'Label').html('Update user group properties');
      } else {
        $('#'+modal_id+'Label').html('Update instance group properties');
      }
      $('#'+modal_id+'Body').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div></div>');
    }
  });
}

function send_update_group_form(modal_id, group_kind)
{
  var group_name = $('#inputGroupname').val();
  if (group_kind == 'instance')
  {
    var data = JSON.stringify({
      'new_group_name': $('#inputNewGroupname').val(),
      'description': $('#inputDescription').val(),
      'user_groups': $('#selectGroups').val()
    });
  } else {
    var data = JSON.stringify({
      'new_group_name': $('#inputNewGroupname').val(),
      'description': $('#inputDescription').val()
    });
  }
  $.ajax({
    url: '/json/settings/group/'+group_kind+'/'+group_name,
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
    },
    data: data,
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      if (group_kind == 'role')
      {
        $('#'+modal_id+'Label').html('Update user group properties');
      } else {
        $('#'+modal_id+'Label').html('Update instance group properties');
      }
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div></div></div>');
    }
  });
}

function load_delete_group_confirm(modal_id, group_kind, group_name)
{
  $.ajax({
    url: '/json/settings/group/'+group_kind+'/'+group_name,
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id+'Info').hide();
      if (group_kind == 'role')
      {
        $('#'+modal_id+'Label').html('Delete user group properties');
      } else {
        $('#'+modal_id+'Label').html('Delete instance group properties');
      }
      var footer_html = '';
      footer_html += '<button type="submit" id="buttonDeleteGroup" class="btn btn-danger">Yes, delete this group</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html(footer_html);
      $('#buttonDeleteGroup').click(function( event ) {
          event.preventDefault();
        send_delete_group(modal_id, data['kind'], data['name']);
      });
    },
    error: function(xhr) {
      if (group_kind == 'role')
      {
        $('#'+modal_id+'label').html('Delete user group confirmation');
      } else {
        $('#'+modal_id+'label').html('Delete instance group confirmation');
      }
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div></div></div>');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    }
  });
}

function send_delete_group(modal_id, group_kind, group_name)
{
  $.ajax({
    url: '/json/settings/delete/group/'+group_kind,
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Body').html('');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({'group_name': group_name}),
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      if (group_kind == 'role')
      {
        $('#'+modal_id+'Label').html('Delete user group confirmation');
      } else {
        $('#'+modal_id+'Label').html('Delete instance group confirmation');
      }
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div></div></div>');
      $('#'+modal_id+'Body').html('');
    }
  });
}

/*
 *  Build the group creation form.
 */
function load_add_group_form(modal_id, group_kind)
{
  if (group_kind == 'role')
  {
    $('#'+modal_id+'Label').html('Add a new user group');
    $('#'+modal_id+'Info').html('');
    var body_html = '';
    body_html += '<form id="formAddGroup">';
    body_html += '  <div class="row">';
    body_html += '    <div class="form-group col-sm-12">';
    body_html += '      <label for="inputNewGroupname" class="control-label">Group name</label>';
    body_html += '      <input type="text" class="form-control" id="inputNewGroupname" placeholder="Group name" />';
    body_html += '    </div>';
    body_html += '  </div>';
    body_html += '  <div class="row">';
    body_html += '    <div class="form-group col-sm-12">';
    body_html += '      <label for="inputDescription" class="control-label">Description</label>';
    body_html += '      <textarea class="form-control" rows="3" placeholder="Description" id="inputDescription"></textarea>';
    body_html += '    </div>';
    body_html += '  </div>';
    body_html += '</form>';
    var footer_html = '';
    footer_html += '<button type="submit" id="submitFormAddGroup" class="btn btn-success">Save</button>';
    footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
    // Write the form.
    $('#'+modal_id+'Body').html(body_html);
    $('#'+modal_id+'Footer').html(footer_html);
    $('#submitFormAddGroup').click(function(){
      $('#formAddGroup').submit();
    });
    $('#formAddGroup').submit(function( event ) {
        event.preventDefault();
      send_add_group_form(modal_id, group_kind);
    });
  } else {
    $.ajax({
      url: '/json/settings/all/group/role',
      type: 'get',
      beforeSend: function(xhr){
        $('#'+modal_id+'Label').html('Processing, please wait...');
        $('#'+modal_id+'Info').html('');
        $('#'+modal_id+'Body').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
        $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
      },
      async: true,
      contentType: "application/json",
      dataType: "json",
      success: function (data) {
        $('#'+modal_id+'Label').html('Add a new instance group');
        $('#'+modal_id+'Info').html('');
        var body_html = '';
        body_html += '<form id="formAddGroup">';
        body_html += '  <div class="row">';
        body_html += '    <div class="form-group col-sm-6">';
        body_html += '      <label for="inputNewGroupname" class="control-label">Group name</label>';
        body_html += '      <input type="text" class="form-control" id="inputNewGroupname" placeholder="New group name" />';
        body_html += '    </div>';
        body_html += '    <div class="form-group col-sm-6">';
        body_html += '      <label for="selectGroups" class="control-label">User groups</label><br />';
        body_html += '      <select id="selectGroups" multiple="multiple">';
        var descriptions = {};
        for (var group of data['groups'])
        {
            body_html += '      <option value="'+group['name']+'">'+group['name']+'</option>';
          descriptions[group['name']] = group['description'];
        }
        body_html += '      </select>';
        body_html += '      <p class="form-text text-muted">Please select the user groups allowed to view instances from this instance group.</p>';
        body_html += '    </div>';
        body_html += '  </div>';
        body_html += '  <div class="row">';
        body_html += '    <div class="form-group col-sm-12">';
        body_html += '      <label for="inputDescription" class="control-label">Description</label>';
        body_html += '      <textarea class="form-control" rows="3" placeholder="Description" id="inputDescription"></textarea>';
        body_html += '    </div>';
        body_html += '  </div>';
        body_html += '</form>';
        var footer_html = '';
        footer_html += '<button type="submit" id="submitFormAddGroup" class="btn btn-success">Save</button>';
        footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
        // Write the form.
        $('#'+modal_id+'Body').html(body_html);
        $('#'+modal_id+'Footer').html(footer_html);
        // Activate multiselect plugin for group selecting.
        $('#selectGroups').multiselect(multiselectOptions);
        // Add group's description as a tooltip.
        $('.multiselect-container li').not('.filter, .group').tooltip({
            placement: 'right',
            container: 'body',
            title: function () {
                var value = $(this).find('input').val();
                return descriptions[value];
            }
        });
        $('#submitFormAddGroup').click(function() {
          $('#formAddGroup').submit()
        });
        $('#formAddGroup').submit(function( event ) {
            event.preventDefault();
          send_add_group_form(modal_id, group_kind);
        });
      },
      error: function(xhr) {
        $('#'+modal_id+'Label').html('Add a new instance group');
        $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
      }
    });

  }
}

function send_add_group_form(modal_id, group_kind)
{
  if (group_kind == 'instance')
  {
    var data = JSON.stringify({
      'new_group_name': $('#inputNewGroupname').val(),
      'description': $('#inputDescription').val(),
      'user_groups': $('#selectGroups').val()
    });
  } else {
    var data = JSON.stringify({
      'new_group_name': $('#inputNewGroupname').val(),
      'description': $('#inputDescription').val()
    });
  }
  $.ajax({
    url: '/json/settings/group/'+group_kind,
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
    },
    data: data,
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      if (group_kind == 'role')
      {
        $('#'+modal_id+'Label').html('Add a new user group');
      } else {
        $('#'+modal_id+'Label').html('Add a new instance group');
      }
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div></div></div>');
    }
  });
}
