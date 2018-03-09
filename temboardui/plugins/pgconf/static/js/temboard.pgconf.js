/*
 * Pgconf plugin
 */

function modal_api_call(api_host, api_port, api_url, api_method, xsession, modal_id, json_params)
{
  $.ajax({
    url: '/proxy/'+api_host+'/'+api_port+api_url,
    type: api_method,
    data: JSON.stringify(json_params),
    beforeSend: function(xhr){
      $('#'+modal_id+'Label').html('Processing, please wait...');
      $('#'+modal_id+'Body').html('<div class="row"><div class="col-4 offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modal_id+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Close</button>');
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
        $('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">Session expired. <a class="btn btn-danger" id="ConfirmOK" href="/server/'+api_host+'/'+api_port+'/login">Back to login page</a></div>');
      }
      else
      {
        $('#'+modal_id+'Body').html('<div class="alert alert-danger" role="alert">ERROR: '+render_xhr_error(xhr)+'</div>');
      }
    }
  });
}

/*
 * Move up/down a table row (tr).
 */
function tr_move(direction, row, tableid)
{
  if (direction == "up")
  {
    if (row.data("line-number") > 1)
      row.insertBefore(row.prev());
  } else {
    row.insertAfter(row.next());
  }
  no_process(tableid);
}

/*
 * Remove a table row.
 */
function tr_remove(row, tableid)
{
  row.remove();
  no_process(tableid);
}

/*
 * Loop through each table row and update line number.
 */
function no_process(tableid)
{
  var i = 0;
  $("#"+tableid+" > tbody > tr").each(function (){
    if ($(this).data("header") == "1")
    {
      // Nothing to do for now.
    } else {
      i += 1;
      $(this).data("line-number", i);
      $(this).children("td").eq(1).children("span.no:first").html(i);
    }
  });
}

function row_edit(row, tableid, modalid, agent_address, agent_port, xsession, force_row_type)
{
  var row_number;
  var edit_mode = false;
  if (row != null)
  {
    // Row editing.
    row_number = row.data("line-number");
    edit_mode = true;
    $("#"+modalid+"ModalLabel").html("Edit line #"+row_number);
  } else {
    // New row.
    row_number = 1;
  }

  $.ajax({
    url: '/proxy/'+agent_address+'/'+agent_port+'/pgconf/hba/options',
    type: 'GET',
    beforeSend: function(xhr){
      xhr.setRequestHeader('X-Session', xsession);
      $('#'+modalid+'Label').html('Processing, please wait...');
      $('#'+modalid+'Info').html('');
      $('#'+modalid+'Body').html('<div class="row"><div class="col-4 offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modalid+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      var n_line = $('#'+tableid+' tr').length;
      var available_row_types = ["comment", "record"];
      var row_type;
      var body_html = '';
      var hba_row = {
        comment: '',
        connection: '',
        database: '',
        user: '',
        address: '',
        auth_method: '',
        auth_options: ''
      };
      if (edit_mode)
      {
        $("#"+modalid+"Label").html("Edit line #"+row_number);
        if (force_row_type != null && available_row_types.indexOf(force_row_type) != -1)
        {
          row_type = force_row_type;
        } else {
          var comment = row.children("td.comment").html();
          row_type = 'comment';
          if (comment == undefined)
          {
            row_type = 'record';
          }
        }
        if (row_type == 'comment')
        {
          hba_row.comment = row.children('.comment').html().replace(/^# +/, "");
        } else {
          hba_row.connection = row.children('.connection').html();
          hba_row.database = row.children('.database').html();
          hba_row.user = row.children('.user').html();
          hba_row.address = row.children('.address').html();
          hba_row.auth_method = row.children('.auth_method:first').children('span:first').html();
          hba_row.auth_options = row.children('.auth_options').html();
        }
      } else {
        $("#"+modalid+"Label").html("Add a new line");
        if (force_row_type != null && available_row_types.indexOf(force_row_type) != -1)
          row_type = force_row_type;
        else
          row_type = 'record';
      }
      body_html += '<form id="formUpdateHBARow">';
      body_html += '  <input type="hidden" name="line_orig" value="'+row_number+'" />';
      body_html += '  <div class="row">';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectRowType" class="control-label">Row type</label>';
      body_html += '      <select id="selectRowType" name="type">';
      body_html += '        <option value="comment" '+((row_type == 'comment')?'selected':null)+'>Comment</option>';
      body_html += '        <option value="record" '+((row_type == 'record')?'selected':null)+'>Record</option>';
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '    <div class="form-group col-sm-6">';
      body_html += '      <label for="selectLineNumber" class="control-label">Line</label>';
      body_html += '      <select id="selectLineNumber" name="line">';
      for (var i = 1; i <= n_line; i++)
      {
        body_html += '      <option value="'+i+'" '+((i == row_number)?'selected':null)+'>'+i+'</option>';
      }
      body_html += '      </select>';
      body_html += '    </div>';
      body_html += '  </div>';

      switch(row_type) {
        case 'comment':
          body_html += get_comment_form(hba_row.comment);
          break;
        case 'record':
          body_html += get_record_form(data,
                  hba_row.connection,
                  hba_row.database,
                  hba_row.user,
                  hba_row.address,
                  hba_row.auth_method,
                  hba_row.auth_options);
          break;
      }

      body_html += '  </div>';
      body_html += '</form>';
      var footer_html = '';
      footer_html += '<button type="submit" id="submitFormUpdateHBARow" class="btn btn-success">Save</button>';
      footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';

      // Write the form.
      $('#'+modalid+'Body').html(body_html);
      $('#'+modalid+'Footer').html(footer_html);
      if (row_type == 'record')
      {

        function getSource(data) {
          var engine, adapter;

          dbnames = new Bloodhound({
                    datumTokenizer: Bloodhound.tokenizers.whitespace,
                    queryTokenizer: Bloodhound.tokenizers.whitespace,
                    local: data
          });
          dbnames.initialize();

          adapter = dbnames.ttAdapter();

          return function(query, cb) {
            if (query == "") {
              cb(data);
            } else {
              adapter(query, cb);
            }
          };
        }
        $('input[name=database]').tagsinput({
          tagClass: 'badge badge-primary',
          typeaheadjs: [
            {
              minLength: 0,
            },{
              limit: 50,
              name: 'dbnames',
              source: getSource(data.databases)
          }]
        });
        $('input[name=user]').tagsinput({
          tagClass: 'badge badge-primary',
          typeaheadjs: [
            {
              minLength: 0,
            },{
              limit: 50,
              name: 'userss',
              source: getSource(data.users)
          }]
        });
        $('#selectConnection').multiselect();
        $('#selectAuthMethod').multiselect();
      }
      $('#selectRowType').multiselect();
      $('#selectRowType').on('change', function() {
        row_edit(row, tableid, modalid, agent_address, agent_port, xsession, this.value)
      });
      $('#selectLineNumber').multiselect();
      $('#formUpdateHBARow').submit(function(event){
        $('#'+modalid).modal('hide');
        update_row_from_form('formUpdateHBARow', tableid, modalid, agent_address, agent_port, xsession, edit_mode);
        event.preventDefault();
      });
      $('#submitFormUpdateHBARow').click(function(){
        $('#'+modalid).modal('hide');
        update_row_from_form('formUpdateHBARow', tableid, modalid, agent_address, agent_port, xsession, edit_mode);
      });
    },
    error: function(xhr) {
      $('#'+modalid+'Label').html('Error');
      $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
    }
  });
}

function get_record_form(hba_options, connection, database, user, address, auth_method, auth_options)
{
  var html_code = '';
  html_code += '<div class="row">';
  html_code += '  <div class="form-group col-sm-6">';
  html_code += '    <label for="selectConnection" class="control-label">Connection</label><br />';
  html_code += '    <select id="selectConnection" name="connection">';
  for (var i in hba_options.connections)
  {
    html_code += '    <option value="'+hba_options.connections[i]+'" '+((hba_options.connections[i] == connection)?'selected':null)+'>'+hba_options.connections[i]+'</option>';
  }
  html_code += '    </select>';
  html_code += '  </div>';
  html_code += '  <div class="form-group col-sm-6">';
  html_code += '    <label for="selectAuthMethod" class="control-label">Authentication method</label></br>';
  html_code += '    <select id="selectAuthMethod" name="auth_method">';
  for (var i in hba_options.auth_methods)
  {
    html_code += '    <option value="'+hba_options.auth_methods[i]+'" '+((hba_options.auth_methods[i] == auth_method)?'selected':null)+'>'+hba_options.auth_methods[i]+'</option>';
  }
  html_code += '    </select>';
  html_code += '  </div>';
  html_code += '</div>';
  html_code += '<div class="row">';
  html_code += '  <div class="form-group col-sm-12">';
  html_code += '    <label for="inputDatabase" class="control-label">Databases</label><br />';
  html_code += '    <input id="inputDatabase" class="form-control form-control-sm" type="text" data-role="tagsinput" name="database" value="'+database+'" />';
  html_code += '  </div>';
  html_code += '</div>';
  html_code += '<div class="row">';
  html_code += '  <div class="form-group col-sm-12">';
  html_code += '    <label for="inputUser" class="control-label">Users</label><br />';
  html_code += '    <input id="inputUser" class="form-control form-control-sm" type="text" data-role="tagsinput" name="user" value="'+user+'" />';
  html_code += '  </div>';
  html_code += '</div>';
  html_code += '<div class="row">';
  html_code += '  <div class="form-group col-sm-12">';
  html_code += '    <label for="inputAddress" class="control-label">Address</label><br />';
  html_code += '    <input id="inputAddress" class="form-control form-control-sm" type="text" name="address" value="'+address+'" />';
  html_code += '  </div>';
  html_code += '</div>';
  html_code += '<div class="row">';
  html_code += '  <div class="form-group col-sm-12">';
  html_code += '    <label for="inputAuthOptions" class="control-label">Authentication options</label><br />';
  html_code += '    <input id="inputAuthOptions" class="form-control form-control-sm" type="text" name="auth_options" value="'+auth_options+'" />';
  html_code += '  </div>';
  html_code += '</div>';
  return html_code;
}

function get_comment_form(comment)
{
  var html_code = '';
  comment = comment.replaceAll(/"/,'&#34;');
  html_code += '<div class="row">';
  html_code += '  <div class="form-group col-sm-12">';
  html_code += '    <label for="inputComment" class="control-label">Comment</label><br />';
  html_code += '    <input id="inputComment" class="form-control form-control-sm" type="text" name="comment" value="'+comment+'" />';
  html_code += '  </div>';
  html_code += '</div>';
  return html_code;
}


function tr_get(line_number, tableid)
{
  var tr;
  $("#"+tableid+" > tbody > tr").each(function (){
    if ($(this).data("line-number") == line_number)
    {
      return tr = $(this);
    }
  });
  return tr;

}

function update_row_from_form(formid, tableid, modalid, agent_address, agent_port, xsession, edit_mode)
{
  var upd_form = $('#'+formid).serializeArray();
  var n_row = {};
  var html_row_new = '';
  var row_pivot = null;
  var row_orig = null;
  var row_new = null;

  // Form serialization.
  for (var i=0; i < upd_form.length; i++)
  {
    var elt = upd_form[i];
    var name = elt.name;
    var value = elt.value;
    n_row[name] = value;
  }
  html_row_new = get_row_html(n_row);
  row_new = $(html_row_new);

  if (edit_mode && n_row.line > n_row.line_orig)
    n_row.line  = (parseInt(n_row.line) + 1);
  n_row.line = parseInt(n_row.line);

  if (edit_mode)
    row_orig = tr_get(n_row.line_orig, tableid);
  row_pivot = tr_get(n_row.line, tableid);

  if (row_pivot == null)
  {
    row_pivot = tr_get((n_row.line-1), tableid);
    if (row_pivot == null)
      row_pivot = $("#"+tableid+" > tbody > tr:first");
    row_new.insertAfter(row_pivot);
  } else {
    row_new.insertBefore(row_pivot);
  }
  row_new.find('.edit').click(function(){
    $('#'+modalid).modal('show');
    $('[data-toggle=popover]').popover('hide');
    var row = $(this).parents("tr:first");
    row_edit(row, tableid, modalid, agent_address, agent_port, xsession, null);
  });
  row_new.find(".up,.down").click(function(){
    var row = $(this).parents("tr:first");
    $(this).tooltip("hide");
    if ($(this).is(".up")) {
      tr_move("up", row, tableid);
    } else {
      tr_move("down", row, tableid);
    }
  });
  row_new.find(".remove").click(function(){
    var row = $(this).parents("tr:first");
    $(this).tooltip("hide");
    tr_remove(row, tableid);
  });
  if (edit_mode)
    row_orig.remove();
  no_process(tableid);
}

function get_row_html(row)
{
  var row_html = '';
  row_html += '<tr data-line-number="'+row.line+'">';
  row_html += ' <td>';
  row_html += '   <button type="button" class="btn btn-outline-secondary btn-sm up" data-toggle="tooltip" data-placement="bottom" title="Move up"><i class="fa fa-arrow-up"></i></button>';
  row_html += '   <button type="button" class="btn btn-outline-secondary btn-sm down" data-toggle="tooltip" data-placement="bottom" title="Move down"><i class="fa fa-arrow-down"></i></button>';
  row_html += ' </td>';
  row_html += ' <td class="text-center"><span class="no">'+row.line+'</span></td>';

  if (row.type == 'comment')
  {
    row_html += '<td colspan="6" class="comment"># '+row.comment+'</td>';
  }
  if (row.type == 'record')
  {
    var auth_method_class = 'success';
    if (row.auth_method == 'trust')
      auth_method_class = 'danger';
    if (row.auth_method == 'password')
      auth_method_class = 'warning';

    row_html += '<td class="connection">'+row.connection+'</td>';
    row_html += '<td class="database">'+row.database+'</td>';
    row_html += '<td class="user">'+row.user+'</td>';
    row_html += '<td class="address">'+row.address+'</td>';
    row_html += '<td class="text-center auth_method"><span class="badge badge-'+auth_method_class+'">'+row.auth_method+'</span></td>';
    row_html += '<td class="auth_options">'+row.auth_options+'</td>';
  }
  row_html += ' <td>';
  row_html += '   <button type="button" class="btn btn-outline-secondary btn-sm edit" data-toggle="tooltip" data-placement="bottom" title="Edit this row"><i class="fa fa-edit"></i></button>';
  row_html += '   <button type="button" class="btn btn-outline-secondary btn-sm remove" data-toggle="tooltip" data-placement="bottom" title="Remove this row"><i class="fa fa-trash-o"></i></button>';
  row_html += ' </td>';
  row_html += '</tr>';
  return row_html;

}

function save_hba_table(tableid, modalid, agent_address, agent_port, xsession)
{
  var hba_rows = [];
  $('#'+tableid+' > tbody > tr').each(function() {
    if ($(this).data("header") != "1")
    {
      var hba_row = {
        comment: '',
        connection: '',
        database: '',
        user: '',
        address: '',
        auth_method: '',
        auth_options: ''
      };
      hba_row.comment = $(this).children('.comment').html();
      if (hba_row.comment == undefined)
      {
        hba_row.connection = $(this).children('.connection').html();
        hba_row.database = $(this).children('.database').html();
        hba_row.user = $(this).children('.user').html();
        hba_row.address = $(this).children('.address').html();
        hba_row.auth_method = $(this).children('.auth_method:first').children('span:first').html();
        hba_row.auth_options = $(this).children('.auth_options').html();
      } else {
        hba_row.comment = hba_row.comment.replace(/^# +/, "");
      }
      hba_rows.push(hba_row);
    }
  });
  var data = {};
  data.new_version = true;
  data.entries = hba_rows;
  $.ajax({
    url: '/proxy/'+agent_address+'/'+agent_port+'/pgconf/hba',
    type: 'POST',
    data: JSON.stringify(data),
    beforeSend: function(xhr){
      xhr.setRequestHeader('X-Session', xsession);

      $('#'+modalid+'Label').html('Processing, please wait...');
      $('#'+modalid+'Info').html('');
      $('#'+modalid+'Body').html('<div class="row"><div class="col-4 offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modalid+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
      $('#'+modalid).modal('show');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modalid+'Label').html('Save and reload configuration');
      $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-success" role="alert"><h4><i class="fa fa-check-circle fa-fw"></i> OK </h4><p>HBA file has been updated and PostgreSQL configuration reloaded.</p></div></div></div>');
      $('#'+modalid+'Footer').html('<button type="button" id="buttonOK" class="btn btn-success" data-dismiss="modal">OK</button>');
      $('#buttonOK').click(function() {
        window.location.replace(window.location.pathname);
      });
    },
    error: function(xhr, textstatus) {
      $('#'+modalid+'Label').html('Error');
      if (xhr.status == 401)
      {
        $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert"><h4><i class="fa fa-ban fa-fw"></i> Error:</h4><p>Session expired.</p></div></div></div>');
        $('#'+modalid+'Footer').html('<a class="btn btn-danger" id="ConfirmOK" href="/server/'+agent_address+'/'+agent_port+'/login">Back to login page</a> <button type="button" id="buttonOK" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
      } else {
        $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert"><h4><i class="fa fa-ban fa-fw"></i> Error:</h4><p>'+render_xhr_error(xhr)+'</p></div></div></div>');
      }
    }
  });
}

function delete_hba(modalid, agent_address, agent_port, xsession, version)
{
  $.ajax({
    url: '/proxy/'+agent_address+'/'+agent_port+'/pgconf/hba/delete?version='+version,
    type: 'GET',
    beforeSend: function(xhr){
      xhr.setRequestHeader('X-Session', xsession);

      $('#'+modalid+'Label').html('Processing, please wait...');
      $('#'+modalid+'Info').html('');
      $('#'+modalid+'Body').html('<div class="row"><div class="col-4 offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
      $('#'+modalid+'Footer').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
      $('#'+modalid).modal('show');
    },
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      $('#'+modalid+'Label').html('Remove HBA file version');
      $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-success" role="alert"><h4><i class="fa fa-check-circle fa-fw"></i> OK </h4><p>Version <b>'+version+'</b> of HBA file has been removed.</p></div></div></div>');
      $('#'+modalid+'Footer').html('<button type="button" id="buttonOK" class="btn btn-success" data-dismiss="modal">OK</button>');
      $('#buttonOK').click(function() {
        window.location.replace(window.location.pathname);
      });
    },
    error: function(xhr, textstatus) {
      $('#'+modalid+'Label').html('Error');
      if (xhr.status == 401)
      {
        $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert"><h4><i class="fa fa-ban fa-fw"></i> Error:</h4><p>Session expired.</p></div></div></div>');
        $('#'+modalid+'Footer').html('<a class="btn btn-danger" id="ConfirmOK" href="/server/'+agent_address+'/'+agent_port+'/login">Back to login page</a> <button type="button" id="buttonOK" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
      } else {
        $('#'+modalid+'Body').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert"><h4><i class="fa fa-ban fa-fw"></i> Error:</h4><p>'+render_xhr_error(xhr)+'</p></div></div></div>');
      }
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

String.prototype.replaceAll = function(search, replacement) {
  var target = this;
  return target.replace(new RegExp(search, 'g'), replacement);
};

function render_xhr_error(xhr)
{
  var error_msg = '';
  if (xhr.status == 0)
  {
    return "Unable to reach frontend API.";
  }
  try {
    error_msg = JSON.parse(xhr.responseText).error;
  } catch(e) {
    error_msg = xhr.responseText;
  }
  return escapeHtml(error_msg);
}
