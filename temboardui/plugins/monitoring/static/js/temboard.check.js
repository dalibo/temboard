/* global apiUrl, checkName, Vue, Dygraph, moment */
$(function() {

  var v = new Vue({
    el: '#check-container',
    data: {
      keys: null
    },
    watch: {}
  });

  function refresh() {
    $.ajax({
      url: apiUrl + "/states/" + checkName + ".json"
    }).success(function(data) {
      v.keys = data;
    }).error(function(error) {
      console.error(error);
    });
  }

  // refresh every 1 min
  window.setInterval(function() {
    refresh();
  }, 60 * 1000);
  refresh();

  Vue.component('monitoring-chart', {
    props: ['check', 'key_'],
    mounted: function() {
      newGraph(this.check, this.key_);
    },
    template: '<div class="monitoring-chart"></div>'
  });

  function newGraph(check, key) {
    var startDate = moment().subtract(2, 'hour');
    var endDate = moment();

    var defaultOptions = {
      axisLabelFontSize: 10,
      yLabelWidth: 14,
      dateWindow: [
        new Date(startDate).getTime(),
        new Date(endDate).getTime()
      ],
      xValueParser: function(x) {
        var m = moment(x);
        return m.toDate().getTime();
      },
    };

    new Dygraph(
      document.getElementById("chart" + key),
      apiUrl+"/../monitoring/data/"+ check + "?key=" + key + "&start="+timestampToIsoDate(startDate)+"&end="+timestampToIsoDate(endDate),
      defaultOptions
    );
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }
});
