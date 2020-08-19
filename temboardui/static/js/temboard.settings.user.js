var multiselectOptions = {
  templates: {
    button: '<button type="button" class="multiselect dropdown-toggle border-secondary" data-toggle="dropdown"><span class="multiselect-selected-text"></span> <b class="caret"></b></button>',
    li: '<li class="dropdown-item"><a href="javascript:void(0);"><label></label></a></li>'
  }
};

/*
 * Load user properties using '/json/settings/user/'+username API
 * and build the update form.
 */
function load_update_user_form(modal_id, username)
{
  $.ajax({
    url: '/json/settings/user/'+username,
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
      $('#'+modal_id+'Label').html('Update user properties');
      var body_html = '';
      body_html += '<form id="formUpdateUser">';
      body_html += '  <input type="hidden" id="inputUsername" value="'+data['role_name']+'" />';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewUsername" class="control-label">Username</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewUsername" placeholder="New Username" value="'+data['role_name']+'" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputEmail" class="control-label">Email</label>';
      body_html += '      <input type="email" class="form-control" id="inputEmail" placeholder="Email" value="'+(data['role_email'] || '')+'">';
      body_html += '      <span class="form-text text-muted small">Leave blank to prevent user from receiving notifications by email.</span>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPassword" class="control-label">Password&#42;</label>';
      body_html += '      <input type="password" class="form-control" id="inputPassword" placeholder="Password" />';
      body_html += '      <input type="password" class="form-control" id="inputPassword2" placeholder="Confirm password" />';
      body_html += '      <p class="form-text text-muted"><small>&#42;: leave this field blank to keep it unchanged.</small></p>';
      body_html += '    </div>';
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
      body_html += '      </select><br />';
      body_html += '      <label for="selectActive" class="control-label">Active</label><br />';
      body_html += '      <select id="selectActive">';
      body_html += '        <option value="No">No</options>';
      sel_active = '';
      if (data['is_active'])
      {
        sel_active = 'selected';
      }
      body_html += '        <option value="yes" '+sel_active+'>Yes</options>';
      body_html += '      </select><br />';
      body_html += '      <label for="selectAdmin" class="control-label">Administrator</label><br />';
      body_html += '      <select id="selectAdmin">';
      body_html += '        <option value="No">No</options>';
      sel_admin = '';
      if (data['is_admin'])
      {
        sel_admin = 'selected';
      }
      body_html += '        <option value="yes" '+sel_admin+'>Yes</options>';
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPhone" class="control-label">Phone</label>';
      body_html += '      <input type="text" class="form-control" id="inputPhone" placeholder="Phone" value="'+(data['role_phone'] || '')+'">';
      body_html += '      <span class="form-text text-muted small">Leave blank to prevent user from receiving notifications by SMS.</span>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<button type="submit" id="submitFormUpdateUser" class="btn btn-success">Save</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
      // Write the form.
      $('#'+modal_id+'Body').html(body_html);
      $('#'+modal_id+'Footer').html(footer_html);
      $('#submitFormUpdateUser').click(function() {
        $('#formUpdateUser').submit()
      });

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
      // Use multiselect style for Active & Admin selects.
      $('#selectActive').multiselect(multiselectOptions);
      $('#selectAdmin').multiselect(multiselectOptions);
      $('#formUpdateUser').submit(function( event ) {
          event.preventDefault();
        send_update_user_form(modal_id);
      });
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Update user properties');
      $('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div>');
    }
  });
}

function send_update_user_form(modal_id)
{
  var username = $('#inputUsername').val();
  $.ajax({
    url: '/json/settings/user/'+username,
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
    },
    data: JSON.stringify({
      'new_username': $('#inputNewUsername').val(),
      'email': $('#inputEmail').val(),
      'phone': $('#inputPhone').val(),
      'password': $('#inputPassword').val(),
      'password2': $('#inputPassword2').val(),
      'groups': $('#selectGroups').val(),
      'is_active': $('#selectActive').val(),
      'is_admin': $('#selectAdmin').val()
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
      $('#'+modal_id+'Label').html('Update user properties');
      $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(xhr.responseText).error+'</div>');
    }
  });
}

function load_delete_user_confirm(modal_id, username)
{
  $.ajax({
    url: '/json/settings/user/'+username,
    type: 'get',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      var footer_html = '';
      footer_html += '<button type="submit" id="buttonDeleteUser" class="btn btn-danger">Yes, delete this user</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
      $('#'+modal_id+'Label').html('Delete user confirmation');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html(footer_html);
      $('#buttonDeleteUser').click(function( event ) {
          event.preventDefault();
        send_delete_user(modal_id, data['role_name']);
      });
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Delete user confirmation');
      $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
      $('#'+modal_id+'Body').html('');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    }
  });
}

function send_delete_user(modal_id, username)
{
  $.ajax({
    url: '/json/settings/delete/user',
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Body').html('');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({ 'username': username }),
    success: function (data) {
      $('#'+modal_id).modal('hide');
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Delete user confirmation');
      $('#'+modal_id+'Info').html('<div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div>');
      $('#'+modal_id+'Body').html('');
    }
  });
}

/*
 *  Build the user creation form.
 */
function load_add_user_form(modal_id)
{
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
      $('#'+modal_id+'Label').html('Add a new user');
      $('#'+modal_id+'Info').html('');
      var body_html = '';
      body_html += '<form id="formAddUser">';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputNewUsername" class="control-label">Username</label>';
      body_html += '      <input type="text" class="form-control" id="inputNewUsername" placeholder="Username" />';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputEmail" class="control-label">Email</label>';
      body_html += '      <input type="email" class="form-control" id="inputEmail" placeholder="Email" />';
      body_html += '      <span class="form-text text-muted small">Leave blank to prevent user from receiving notifications by email.</span>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPassword" class="control-label">Password&#42;</label>';
      body_html += '      <input type="password" class="form-control" id="inputPassword" placeholder="Password" />';
      body_html += '      <input type="password" class="form-control" id="inputPassword2" placeholder="Confirm password" />';
      body_html += '      <p class="form-text text-muted"><small>&#42;: leave this field blank to keep it unchanged.</small></p>';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectGroups" class="control-label">Groups</label><br />';
      body_html += '      <select id="selectGroups" multiple="multiple">';
      var descriptions = {};
      for (var group of data['groups'])
      {
          body_html += '      <option value="'+group['name']+'">'+group['name']+'</option>';
        descriptions[group['name']] = group['description'];
      }
      body_html += '      </select><br />';
      body_html += '      <label for="selectActive" class="control-label">Active</label><br />';
      body_html += '      <select id="selectActive">';
      body_html += '        <option value="yes" selected>Yes</options>';
      body_html += '        <option value="No">No</options>';
      body_html += '      </select><br />';
      body_html += '      <label for="selectAdmin" class="control-label">Administrator</label><br />';
      body_html += '      <select id="selectAdmin">';
      body_html += '        <option value="No" selected>No</options>';
      body_html += '        <option value="yes">Yes</options>';
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="inputPhone" class="control-label">Phone</label>';
      body_html += '      <input type="text" class="form-control" id="inputPhone" placeholder="Phone">';
      body_html += '      <span class="form-text text-muted small">Leave blank to prevent user from receiving notifications by SMS.</span>';
      body_html += '    </div>';
      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<button type="submit" id="submitFormAddUser" class="btn btn-success">Save</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
      // Write the form.
      $('#'+modal_id+'Body').html(body_html);
      $('#'+modal_id+'Footer').html(footer_html);
      $('#submitFormAddUser').click(function() {
        $('#formAddUser').submit()
      });

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
      // Use multiselect style for Active & Admin selects.
      $('#selectActive').multiselect(multiselectOptions);
      $('#selectAdmin').multiselect(multiselectOptions);
      $('#formAddUser').submit(function( event ) {
          event.preventDefault();
        send_add_user_form(modal_id);
      });
    },
    error: function(xhr) {
      $('#'+modal_id+'Label').html('Add a new user');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
    }
  });
}

function send_add_user_form(modal_id)
{
  $.ajax({
    url: '/json/settings/user',
    type: 'post',
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
    },
    data: JSON.stringify({
      'new_username': $('#inputNewUsername').val(),
      'email': $('#inputEmail').val(),
      'phone': $('#inputPhone').val(),
      'password': $('#inputPassword').val(),
      'password2': $('#inputPassword2').val(),
      'groups': $('#selectGroups').val(),
      'is_active': $('#selectActive').val(),
      'is_admin': $('#selectAdmin').val()
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
      $('#'+modal_id+'Label').html('Add a new user');
      $('#'+modal_id+'Info').html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
    }
  });
}

function sendEmail() {
  $.ajax({
    url: '/json/test_email',
    type: 'post',
    data: JSON.stringify({
      email: $('#inputTestEmail').val()
    }),
    success: function(data) {
      var msg = 'Test email successfully sent';
      msg += '\nIf the email is not received, please have a look at your SMTP server logs';
      alert(msg);
    },
    error: function(xhr) {
      var msg = 'Mail could not be sent.';
      if (xhr.responseText) {
        msg += '\nError: ';
        msg += escapeHtml(JSON.parse(xhr.responseText).error);
      }
      alert(msg);
    }
  });
}

function sendSms() {
  $.ajax({
    url: '/json/test_sms',
    type: 'post',
    data: JSON.stringify({
      phone: $('#inputTestPhone').val()
    }),
    success: function(data) {
      alert("Test SMS sent");
    },
    error: function(xhr) {
      alert("SMS could not be sent.\nError: " + escapeHtml(JSON.parse(xhr.responseText).error));
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
