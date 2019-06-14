(window.webpackJsonp=window.webpackJsonp||[]).push([["settings.group"],{"./temboardui/static/js/temboard.settings.group.js":function(e,t,o){"use strict";o.r(t),function(e){var t=o("./node_modules/datatables.net-bs4/js/dataTables.bootstrap4.js"),s=o.n(t);o("./node_modules/datatables.net-bs4/css/dataTables.bootstrap4.css");function r(t,o,s){e.ajax({url:"/json/settings/group/"+o+"/"+s,type:"get",beforeSend:function(o){e("#"+t+"Label").html("Processing, please wait..."),e("#"+t+"Info").html(""),e("#"+t+"Body").html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>'),e("#"+t+"Footer").html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>')},async:!0,contentType:"application/json",dataType:"json",success:function(s){"role"==s.kind?e("#"+t+"Label").html("Update user group properties"):e("#"+t+"Label").html("Update instance group properties");var r="";if(r+='<form id="formUpdateGroup">',r+='  <input type="hidden" id="inputGroupname" value="'+s.name+'" />',r+='  <div class="row">',r+='    <div class="form-group col-sm-6">',r+='      <label for="inputNewGroupname" class="control-label">Group name</label>',r+='      <input type="text" class="form-control" id="inputNewGroupname" placeholder="New group name" value="'+s.name+'" />',r+="    </div>","instance"==o){r+='    <div class="form-group col-sm-6">',r+='      <label for="selectGroups" class="control-label">User groups</label><br />',r+='      <select id="selectGroups" multiple="multiple">';var a={},n="";for(var i in s.user_groups)n="",s.in_groups.indexOf(i.name)>-1&&(n="selected"),r+='      <option value="'+i.name+'" '+n+">"+i.name+"</option>",a[i.name]=i.description;r+="      </select>",r+='      <p class="form-text text-muted">Please select the user groups allowed to view instances from this instance group.</p>',r+="    </div>"}r+="  </div>",r+='  <div class="row">',r+='    <div class="form-group col-sm-12">',r+='      <label for="inputDescription" class="control-label">Description</label>',r+='      <textarea class="form-control" rows="3" placeholder="Description" id="inputDescription">'+s.description+"</textarea>",r+="    </div>",r+="  </div>",r+="</form>";e("#"+t+"Body").html(r),e("#"+t+"Footer").html('<button type="submit" id="submitFormUpdateGroup" class="btn btn-success">Save</button> <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>'),"instance"==o&&(e("#selectGroups").multiselect(),e(".multiselect-container li").not(".filter, .group").tooltip({placement:"right",container:"body",title:function(){var t=e(this).find("input").val();return a[t]}})),e("#submitFormUpdateGroup").click(function(){e("#formUpdateGroup").submit()}),e("#formUpdateGroup").submit(function(o){o.preventDefault(),function(t,o){var s=e("#inputGroupname").val();if("instance"==o)var r=JSON.stringify({new_group_name:e("#inputNewGroupname").val(),description:e("#inputDescription").val(),user_groups:e("#selectGroups").val()});else var r=JSON.stringify({new_group_name:e("#inputNewGroupname").val(),description:e("#inputDescription").val()});e.ajax({url:"/json/settings/group/"+o+"/"+s,type:"post",beforeSend:function(o){e("#"+t+"Label").html("Processing, please wait..."),e("#"+t+"Info").html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>')},data:r,async:!0,contentType:"application/json",dataType:"json",success:function(o){e("#"+t).modal("hide");var s=window.location.href;window.location.replace(s)},error:function(s){"role"==o?e("#"+t+"Label").html("Update user group properties"):e("#"+t+"Label").html("Update instance group properties"),e("#"+t+"Info").html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(s.responseText).error+"</div></div></div>")}})}(t,s.kind)})},error:function(s){"role"==o?e("#"+t+"Label").html("Update user group properties"):e("#"+t+"Label").html("Update instance group properties"),e("#"+t+"Body").html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(s.responseText).error+"</div></div>")}})}function a(t,o,s){e.ajax({url:"/json/settings/group/"+o+"/"+s,type:"get",beforeSend:function(o){e("#"+t+"Label").html("Processing, please wait..."),e("#"+t+"Info").html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>'),e("#"+t+"Footer").html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>')},async:!0,contentType:"application/json",dataType:"json",success:function(s){e("#"+t+"Info").hide(),"role"==o?e("#"+t+"Label").html("Delete user group properties"):e("#"+t+"Label").html("Delete instance group properties");e("#"+t+"Body").html(""),e("#"+t+"Footer").html('<button type="submit" id="buttonDeleteGroup" class="btn btn-danger">Yes, delete this group</button> <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>'),e("#buttonDeleteGroup").click(function(o){o.preventDefault(),function(t,o,s){e.ajax({url:"/json/settings/delete/group/"+o,type:"post",beforeSend:function(o){e("#"+t+"Label").html("Processing, please wait..."),e("#"+t+"Info").html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>'),e("#"+t+"Body").html("")},async:!0,contentType:"application/json",dataType:"json",data:JSON.stringify({group_name:s}),success:function(o){e("#"+t).modal("hide");var s=window.location.href;window.location.replace(s)},error:function(s){"role"==o?e("#"+t+"Label").html("Delete user group confirmation"):e("#"+t+"Label").html("Delete instance group confirmation"),e("#"+t+"Info").html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(s.responseText).error+"</div></div></div>"),e("#"+t+"Body").html("")}})}(t,s.kind,s.name)})},error:function(s){"role"==o?e("#"+t+"label").html("Delete user group confirmation"):e("#"+t+"label").html("Delete instance group confirmation"),e("#"+t+"Info").html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(s.responseText).error+"</div></div></div>"),e("#"+t+"Body").html(""),e("#"+t+"Footer").html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>')}})}function n(t,o){if("instance"==o)var s=JSON.stringify({new_group_name:e("#inputNewGroupname").val(),description:e("#inputDescription").val(),user_groups:e("#selectGroups").val()});else s=JSON.stringify({new_group_name:e("#inputNewGroupname").val(),description:e("#inputDescription").val()});e.ajax({url:"/json/settings/group/"+o,type:"post",beforeSend:function(o){e("#"+t+"Label").html("Processing, please wait..."),e("#"+t+"Info").html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>')},data:s,async:!0,contentType:"application/json",dataType:"json",success:function(o){e("#"+t).modal("hide");var s=window.location.href;window.location.replace(s)},error:function(s){"role"==o?e("#"+t+"Label").html("Add a new user group"):e("#"+t+"Label").html("Add a new instance group"),e("#"+t+"Info").html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+JSON.parse(s.responseText).error+"</div></div></div>")}})}s()(window,e),e(document).ready(function(){e("#tableGroups").DataTable({stateSave:!0}),e("#buttonLoadAddGroupForm").click(function(){var t,o;e("#GroupModal").modal("show"),e("[data-toggle=popover]").popover("hide"),t="GroupModal","role"==(o="{{group_kind}}")?(e("#"+t+"Label").html("Add a new user group"),e("#"+t+"Info").html(""),e("#"+t+"Body").html('<form id="formAddGroup">  <div class="row">    <div class="form-group col-sm-12">      <label for="inputNewGroupname" class="control-label">Group name</label>      <input type="text" class="form-control" id="inputNewGroupname" placeholder="Group name" />    </div>  </div>  <div class="row">    <div class="form-group col-sm-12">      <label for="inputDescription" class="control-label">Description</label>      <textarea class="form-control" rows="3" placeholder="Description" id="inputDescription"></textarea>    </div>  </div></form>'),e("#"+t+"Footer").html('<button type="submit" id="submitFormAddGroup" class="btn btn-success">Save</button> <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>'),e("#submitFormAddGroup").click(function(){e("#formAddGroup").submit()}),e("#formAddGroup").submit(function(e){e.preventDefault(),n(t,o)})):e.ajax({url:"/json/settings/all/group/role",type:"get",beforeSend:function(o){e("#"+t+"Label").html("Processing, please wait..."),e("#"+t+"Info").html(""),e("#"+t+"Body").html('<div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>'),e("#"+t+"Footer").html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>')},async:!0,contentType:"application/json",dataType:"json",success:function(s){e("#"+t+"Label").html("Add a new instance group"),e("#"+t+"Info").html("");var r="";r+='<form id="formAddGroup">',r+='  <div class="row">',r+='    <div class="form-group col-sm-6">',r+='      <label for="inputNewGroupname" class="control-label">Group name</label>',r+='      <input type="text" class="form-control" id="inputNewGroupname" placeholder="New group name" />',r+="    </div>",r+='    <div class="form-group col-sm-6">',r+='      <label for="selectGroups" class="control-label">User groups</label><br />',r+='      <select id="selectGroups" multiple="multiple">';var a={};for(var i in s.groups)r+='      <option value="'+i.name+'">'+i.name+"</option>",a[i.name]=i.description;r+="      </select>",r+='      <p class="form-text text-muted">Please select the user groups allowed to view instances from this instance group.</p>',r+="    </div>",r+="  </div>",r+='  <div class="row">',r+='    <div class="form-group col-sm-12">',r+='      <label for="inputDescription" class="control-label">Description</label>',r+='      <textarea class="form-control" rows="3" placeholder="Description" id="inputDescription"></textarea>',r+="    </div>",r+="  </div>",r+="</form>",e("#"+t+"Body").html(r),e("#"+t+"Footer").html('<button type="submit" id="submitFormAddGroup" class="btn btn-success">Save</button> <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>'),e("#selectGroups").multiselect(),e(".multiselect-container li").not(".filter, .group").tooltip({placement:"right",container:"body",title:function(){var t=e(this).find("input").val();return a[t]}}),e("#submitFormAddGroup").click(function(){e("#formAddGroup").submit()}),e("#formAddGroup").submit(function(e){e.preventDefault(),n(t,o)})},error:function(o){e("#"+t+"Label").html("Add a new instance group"),e("#"+t+"Info").html('<div class="row"><div class="col-md-12"><div class="alert alert-danger" role="alert">ERROR: '+escapeHtml(JSON.parse(o.responseText).error)+"</div></div></div>")}})}),e(document).on("click","[data-action=edit]",function(){e("#GroupModal").modal("show"),e("[data-toggle=popover]").popover("hide"),r("GroupModal","{{group_kind}}",e(this).data("group_name"))}),e(document).on("click","[data-action=delete]",function(){e("#GroupModal").modal("show"),e("[data-toggle=popover]").popover("hide"),a("GroupModal","{{group_kind}}",e(this).data("group_name"))})})}.call(this,o("./node_modules/jquery/dist/jquery.js"))}},[["./temboardui/static/js/temboard.settings.group.js","runtime","vendors~activity~base~notifications~settings.group~settings.instance~settings.user","vendors~activity~notifications~settings.group~settings.instance~settings.user"]]]);