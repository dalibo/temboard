colors = {
  blue: "#5DA5DA",
  blue2: "#226191",
  green: "#60BD68",
  red: "#F15854",
  gray: "#4D4D4D",
  light_gray: "#AAAAAA",
  orange: "#FAA43A",
}

function new_graph(id, title, api, api_url, options, start_date, end_date)
{
  var html_chart_panel = '';
  html_chart_panel += '<div class="panel panel-default">';
  html_chart_panel += ' <div class="panel-heading">';
  html_chart_panel += title;
  html_chart_panel += ' </div>';
  html_chart_panel += ' <div class="panel-body">';
  html_chart_panel += '   <div id="info'+id+'"></div>';
  html_chart_panel += '   <div id="legend'+id+'" class="legend-chart"><div class="row"><div class="col-md-4 col-md-offset-4"><div class="progress"><div class="progress-bar progress-bar-striped" style="width: 100%;">Loading, please wait ...</div></div></div></div></div>';
  html_chart_panel += '   <div id="chart'+id+'" class="monitoring-chart"></div>';
  html_chart_panel += '   <div id="visibility'+id+'" class="visibility-chart"></div>';
  html_chart_panel += ' </div>';
  html_chart_panel += '</div>';
  $('#'+id).html(html_chart_panel);
  var default_options = {
      axisLabelFontSize: 10,
      yLabelWidth: 14,
      legend: "always",
      labelsDiv: "legend"+id,
      labelsKMB: true,
      animatedZooms: true,
      gridLineColor: '#DDDDDD',
      dateWindow: [
        new Date(start_date).getTime(),
        new Date(end_date).getTime()
      ],
      xValueParser: function(x) {
        var m = moment(x);
        return m.toDate().getTime();
      },
      drawCallback: function(g, is_initial) {
        if (g.numRows() == 0)
        {
          $('#info'+id).html('<center><i>No data available</i></center>');
          $('#legend'+id).hide();
          $('#chart'+id).hide();
          $('#visibility'+id).hide();
        } else {
          add_visibility_cb(id, g, is_initial);
          $('#info'+id).html('');
          $('#legend'+id).show();
          $('#chart'+id).show();
          $('#visibility'+id).show();
        }
      },
      zoomCallback: function(minDate, maxDate, yRanges) {
        synchronize_zoom(minDate, maxDate, api_url);
      },
      // change interaction model in order to be able to capture the end of
      // panning
      // Dygraphs doesn't provide any panCallback unfortunately
      interactionModel: {
        mousedown: function (event, g, context) {
          context.initializeMouseDown(event, g, context);
          if (event.shiftKey) {
            Dygraph.startPan(event, g, context);
          } else {
            Dygraph.startZoom(event, g, context);
          }
        },
        mousemove: function (event, g, context) {
          if (context.isPanning) {
            Dygraph.movePan(event, g, context);
          } else if (context.isZooming) {
            Dygraph.moveZoom(event, g, context);
          }
        },
        mouseup: function (event, g, context) {
          if (context.isPanning) {
            Dygraph.endPan(event, g, context);
            var dates = g.dateWindow_;
            // synchronize charts on pan end
            synchronize_zoom(dates[0], dates[1], api_url);
          } else if (context.isZooming) {
            Dygraph.endZoom(event, g, context);
            // don't do the same since zoom is animated
            // zoomCallback will do the job
          }
        }
      }
  }

  for (var attrname in options)
  {
    default_options[attrname] = options[attrname];
  }
  var g = new Dygraph(
    document.getElementById("chart"+id),
    api_url+"/"+api+"?start="+timestampToIsoDate(start_date)+"&end="+timestampToIsoDate(end_date)+"&noerror=1",
    default_options
  );
  return g;
}

function timestampToIsoDate(epoch_ms)
{
  var ndate = new Date(epoch_ms);
  return ndate.toISOString();
}

function add_visibility_cb(chart_id, g, is_initial)
{
  if (!is_initial)
    return;

  var nb_legend_item = 0;
  var visibility_html = ''
  var cb_ids = [];
  $('#legend'+chart_id).children('span').each(function() {
    visibility_html += '<input type="checkbox" id="'+chart_id+'CB'+nb_legend_item+'" checked>';
    visibility_html += '<label for="'+chart_id+'CB'+nb_legend_item+'" style="'+$(this).attr('style')+'"> '+$(this).text()+'</label>  ';
    cb_ids.push(chart_id+'CB'+nb_legend_item);
    nb_legend_item += 1;
  });
  $('#visibility'+chart_id).html(visibility_html);
  var nb = 0;
  for(var i in cb_ids) {
    $('#'+cb_ids[i]).change(function() {
      g.setVisibility(parseInt($(this).attr('id').replace(chart_id+'CB', '')), $(this).is(':checked'));
    });
    nb += 1;
  }
}


function updateDateRange(start, end) {
  $('#daterange span').html(
    start.format(dateFormat) + ' - ' + end.format(dateFormat));
  window.location.hash = 'start=' + start + '&end=' + end;
}

function getHashParams() {

  var hashParams = {};
  var e;
  var a = /\+/g;  // Regex for replacing addition symbol with a space
  var r = /([^&;=]+)=?([^&;]*)/g;
  var d = function (s) {
    return decodeURIComponent(s.replace(a, " "));
  };
  var q = window.location.hash.substring(1);

  while (e = r.exec(q)) {
    hashParams[d(e[1])] = d(e[2]);
  }

  return hashParams;
}

function synchronize_zoom(start_date, end_date, api_url, silent)
{
  var picker = $('#daterange').data('daterangepicker');
  if (!silent) {
    // update picker
    picker.setStartDate(moment(start_date));
    picker.setEndDate(moment(end_date));
  }

  // get new date from picker (may be rounded)
  start_date = picker.startDate;
  end_date = picker.endDate;

  updateDateRange(start_date, end_date);

  for(var i in sync_graphs)
  {
    // update the date range
    sync_graphs[i].dygraph.updateOptions({
      dateWindow: [start_date, end_date]
    });
    // load the date for the given range
    sync_graphs[i].dygraph.updateOptions({
      file: api_url+"/"+sync_graphs[i].api+"?start="+timestampToIsoDate(start_date)+"&end="+timestampToIsoDate(end_date)+"&noerror=1"
    }, false);
  }
}
