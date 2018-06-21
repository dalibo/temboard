$(function() {
  "use strict";

  var request = null;
  var intervalId;
  var intervalDuration = 2;

  $('#intervalDuration').html(intervalDuration);

  var el = $('#tableActivity');

  function onCreatedCellDangerY(td, cellData) {
    if (cellData == 'Y') {
      $(td).addClass('text-danger font-weight-bold');
    }
  }

  var checkboxTooltip = "Select to terminate";
  var checkboxDisabledTooltip = "Disable auto-refresh and select to terminate";

  var columns = [
    {
      orderable: false,
      className: 'text-center',
      data: function(row, type, val, meta) {
        var disabled = intervalId ? 'disabled' : '';
        var title = disabled ? checkboxDisabledTooltip : checkboxTooltip;
        var html = '<input type="checkbox" ' + disabled + ' class="input-xs" data-pid="' + row.pid + '"';
        html += 'title="' + title + '"';
        html += ' />';
        return html;
      }
    },
    {title: 'PID', data: 'pid', className: 'text-right', orderable: false},
    {title: 'Database', data: 'database', orderable: false},
    {title: 'User', data: 'user', orderable: false},
    {title: 'CPU', data: 'cpu', className: 'text-right'},
    {title: 'mem', data: 'memory', className: 'text-right'},
    {
      title: 'Read/s',
      data: function(row) {
        return row.read_s.human2bytes();
      },
      render: function(data, type, row) {
        return type == 'display' ? row.read_s : data;
      },
      className: 'text-right'
    },
    {
      title: 'Write/s',
      data: function(row) {
        return row.write_s.human2bytes();
      },
      render: function(data, type, row) {
        return type == 'display' ? row.write_s : data;
      },
      className: 'text-right'
    },
    {
      title: 'IOW',
      data: 'iow',
      className: 'text-center',
      createdCell: onCreatedCellDangerY
    }
  ];
  if (activityMode == 'running') {
    columns = columns.concat([
      {
        title: 'W',
        data: 'wait',
        className: 'text-center',
        createdCell: onCreatedCellDangerY
      }
    ]);
  } else {
    columns = columns.concat([
      {title: 'Lock Rel.', data: 'relation', className: 'text-right', orderable: false},
      {title: 'Lock Mode', data: 'mode', orderable: false},
      {title: 'Lock Type', data: 'type', orderable: false}
    ]);
  }

  var stateMaxLength = 12;
  columns = columns.concat([
    {
      title: 'State',
      data: function(row, type, val, meta) {
        return row.state && row.state.trunc(stateMaxLength);
      },
      className: 'text-center',
      createdCell: function(td, cellData, rowData, row, col) {
        var cls = '';
        switch (rowData.state) {
          case 'active':
            cls = 'text-success font-weight-bold';
            break;
          case 'idle in transaction':
          case 'idle in transaction (aborted)':
            cls = 'text-danger font-weight-bold';
            break;
        }
        $(td).addClass(cls);
        if (rowData.state.length > stateMaxLength) {
          $(td).attr('title', rowData.state);
        }
      }
    },
    {
      title: 'Time',
      className: 'text-right',
      data: 'duration',
      render: function(data, type, row) {
        return type === 'display' ? data + ' s' : data;
      }
    },
    {
      title: 'Query',
      className: 'query',
      data: function(row, type, val, meta) {
        return '<pre>' +
                 '<code class="sql">' + row.query + '</code>' +
               '</pre>';
      },
      createdCell: function(td, cellData) {
        $(td).attr('data-toggle', 'popover').attr('data-trigger', 'hover');
        $(td).mouseover(function() {
          var copyEl = $('<span>', {
            'class': 'copy position-absolute right-0 pr-1 pl-1 bg-secondary text-white rounded',
            html: 'Click to copy'
          });
          $(this).prepend(copyEl);
        });
        $(td).mouseout(function() {
          $(this).find('.copy').remove();
        });
      }
    }
  ]);

  var table = el.DataTable({
    paging: false,
    stateSave: true,
    lengthChange: false,
    autoWidth: false,
    order: [[columns.length - 2, 'desc']], /* order by duration */
    columns: columns,
    dom: 't' // only show table
  });

  function load() {
    var url_end = activityMode != 'running' ?  '/' + activityMode : '';
    // abort any pending request
    request && request.abort();
    request = $.ajax({
      url: '/proxy/'+agent_address+'/'+agent_port+'/activity'+url_end,
      type: 'GET',
      beforeSend: function(xhr) {
        xhr.setRequestHeader('X-Session', xsession);
        $('#loadingIndicator').removeClass('d-none');
      },
      async: true,
      contentType: "application/json",
      success: function (data) {
        updateActivity(data.rows);
      },
      error: function(xhr) {
        if (xhr.status == 401) {
          $('#modalError').html(html_error_modal(401, 'Session expired'));
          $('#ErrorModalFooter').html('<a class="btn btn-outline-secondary" id="aBackLogin">Back to login page</a>');
          $('#aBackLogin').attr('href', '/server/'+agent_address+'/'+agent_port+'/login');
          $('#ErrorModal').modal('show');
        } else {
          var code = xhr.status;
          var error = 'Internal error.';
          if (code > 0) {
            error = escapeHtml(JSON.parse(xhr.responseText).error);
          } else {
            code = '';
          }
          $('#modalError').html(html_error_modal(code, error));
          $('#ErrorModal').modal('show');
        }
      },
      complete: function() {
        $('#ErrorModal').modal('hide');
        $('#loadingIndicator').addClass('d-none');
      }
    });
  }

  function updateActivity(data) {
    $('[data-toggle=popover]').popover('hide');
    table.clear();
    table.rows.add(data).draw();
    $('pre code').each(function(i, block) {
      hljs.highlightBlock(block);
    });

    $('[data-toggle="popover"]').popover({
      html: true,
      content: function() {
        return $(this).find('pre').html();
      },
      template: '<div class="popover sql" role="tooltip"><div class="arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>'
    });
  }

  function html_error_modal(code, error) {
    var error_html = '';
    error_html += '<div class="modal" id="ErrorModal" tabindex="-1" role="dialog" aria-labelledby="ErrorModalLabel" aria-hidden="true">';
    error_html += '   <div class="modal-dialog">';
    error_html += '     <div class="modal-content">';
    error_html += '       <div class="modal-header">';
    error_html += '         <h4 class="modal-title" id="ErrorModalLabel">Error '+code+'</h4>';
    error_html += '         <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
    error_html += '       </div>';
    error_html += '       <div class="modal-body">';
    error_html += '         <div class="alert alert-danger" role="alert">'+error+'</div>';
    error_html += '       </div>';
    error_html += '       <div class="modal-footer" id="ErrorModalFooter">';
    error_html += '         <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Close</button>';
    error_html += '       </div>';
    error_html += '     </div>';
    error_html += '   </div>';
    error_html += '</div>';
    return error_html;
  }

  function pause() {
    request && request.abort();
    $('#autoRefreshCheckbox').prop('checked', false);
    $('#refreshButton').prop('disabled', false);
    $('#tableActivity input[type=checkbox]').each(function () {
      $(this).attr('disabled', false);
      $(this).attr('title', checkboxTooltip);
    });
    window.clearInterval(intervalId);
    intervalId = null;
  }

  function play() {
    $('#autoRefreshCheckbox').prop('checked', true)
    $('#refreshButton').prop('disabled', true);
    $('#killButton').addClass('disabled');
    $('#tableActivity input:checked').each(function () {
      $(this).attr('checked', false);
    });
    $('#tableActivity input[type=checkbox]').each(function () {
      $(this).attr('disabled', true);
      $(this).attr('title', checkboxDisabledTooltip);
    });
    load();
    intervalId = window.setInterval(load, intervalDuration * 1000);
  }

  $('#autoRefreshCheckbox').change(function() {
    if ($(this).prop('checked')) {
      play();
    } else {
      pause();
    }
  });

  // Launch once
  play();

  $('#refreshButton').click(load);

  // show the kill button only when backends have been selected
  $(document.body).on('click', 'input[type=checkbox]', function() {
    $('#killButton').toggleClass('disabled', $('#tableActivity input:checked').length === 0);
  });

  $('#killButton').click(function terminate() {
    var pids = [];
    $('#tableActivity input:checked').each(function () {
      pids.push($(this).data('pid'));
    });
    if (pids.length === 0) {
      return;
    }
    $('#Modal').modal('show');
    $('#ModalLabel').html('Terminate backend');
    var pids_html = '';
    for(var i = 0; i < pids.length; i++) {
      pids_html += '<span class="badge badge-primary">'+pids[i]+'</span> ';
    }
    $('#ModalInfo').html(pids_html);
    var footer_html = '';
    footer_html += '<button type="button" id="submitKill" class="btn btn-danger">Yes, terminate</button>';
    footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
    $('#ModalFooter').html(footer_html);
    $('#submitKill').click(function(){
      $.ajax({
        url: '/proxy/'+agent_address+'/'+agent_port+'/activity/kill',
        type: 'POST',
        beforeSend: function(xhr){
          xhr.setRequestHeader('X-Session', xsession);
          $('#ModalInfo').html('<div class="row"><div class="col-4 offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Please wait ...</div></div></div></div>');
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
            $('#ModalInfo').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert">Error: Session expired.</div></div></div>');
            var footer_html = '';
            footer_html += '<button type="button" id="buttonBackLogin" class="btn btn-success">Back to login page</button>';
            footer_html += ' <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>';
            $('#ModalFooter').html(footer_html);
            $('#buttonBackLogin').attr('href', '/server/'+agent_address+'/'+agent_port+'/login');
          }
          else
          {
            $('#ModalInfo').html('<div class="row"><div class="col-12"><div class="alert alert-danger" role="alert">Error: '+escapeHtml(JSON.parse(xhr.responseText).error)+'</div></div></div>');
            $('#ModalFooter').html('<button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>');
          }
        }
      });
    });
  });

  var stateFilters = $('#state-filter input[type=checkbox]');
  stateFilters.change(table.draw);

  /* State filtering function */
  $.fn.dataTable.ext.search.push(
    function stateFilter(settings, data, index, rawData) {
      var states = [];
      stateFilters.each(function(index, el) {
        var input = $(el);
        if (input.prop('checked')) {
          states.push(input.val());
        }
      });
      return states.indexOf(rawData.state) > -1;
    }
  );

  var searchFilter = $('#searchFilter');
  searchFilter.keyup(table.draw);
  /* Custom filtering function */
  $.fn.dataTable.ext.search.push(
    function searchFilterFn(settings, data) {
      var criteria = searchFilter.val();
      var i = 0;
      var len = data.length;
      for (i; i < len; i++) {
        if (data[i].toUpperCase().indexOf(criteria.toUpperCase()) != -1) {
          return true;
        }
      }
      return false;
    }
  );

  /**
   * Find the index of the column for a given title
   */
  function getColumnIndex(title) {
    var i = 0;
    var len = columns.length;
    for (i; i < len; i++) {
      var col = columns[i];
      if (col.title == title) {
        return i;
      }
    }
    return undefined;
  }

  // copy to clipboard on sql cell click
  $('#tableActivity').on('click', '.sql', function(e) {
    e.preventDefault();
    var range = document.createRange();
    var sel = window.getSelection();
    range.selectNodeContents(this);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand("copy");
    $(this).parents('td').find('.copy').html('Copied to clipboard');
  });
});

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

String.prototype.trunc = String.prototype.trunc || function(n){
  return (this.length > n) ? this.substr(0, n-1) + '&hellip;' : this;
};

String.prototype.human2bytes = String.prototype.human2bytes || function() {
  var val = parseFloat(this);
  if (typeof val == 'number') {
    var suffix = this.slice(-1);
    var suffixes = ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'];
    return val * Math.pow(2, suffixes.indexOf(suffix) * 10);
  }
  return this;
};
