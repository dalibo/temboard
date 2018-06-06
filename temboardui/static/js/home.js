/* global instances, Vue, Dygraph, moment */
$(function() {

  Vue.component('sparkline', {
    props: ['instance', 'metric'],
    mounted: createChart,
    template: '<div></div>'
  });

  new Vue({
    el: '#instances',
    data: {
      instances: instances
    },
    methods: {
      hasMonitoring: function(instance) {
        var plugins = instance.plugins.map(function(plugin) {
          return plugin.plugin_name;
        });
        return plugins.indexOf('monitoring') != -1;
      }
    }
  });

  function createChart() {
    var api_url = ['/server', this.instance.agent_address, this.instance.agent_port, 'monitoring'].join('/');

    var start = moment().subtract(1, 'hours').toISOString();
    var end = moment().toISOString();
    var defaultOptions = {
      axes: {
        x: {
          drawGrid: false,
          axisLabelFontSize: 9,
          axisLabelColor: '#999',
          pixelsPerLabel: 40,
          gridLineColor: '#dfdfdf',
          axisLineColor: '#dfdfdf'
          //drawAxis: false
        },
        y: {
          axisLabelFontSize: 9,
          axisLabelColor: '#999',
          axisLabelWidth: 15,
          pixelsPerLabel: 10,
          drawAxesAtZero: true,
          includeZero: true,
          axisLineColor: '#dfdfdf',
          gridLineColor: '#dfdfdf'
        }
      },
      legend: 'never',
      xValueParser: function(x) {
        var m = moment(x);
        return m.toDate().getTime();
      },
      highlightCircleSize: 0,
      interactionModel: {}
    };

    var options = defaultOptions;
    switch (this.metric) {
    case 'load1':
      options = $.extend({colors: ['#FAA43A']}, options);
      break;
    case 'tps':
      options = $.extend({colors: ['#50BD68', '#F15854']}, options);
      break;
    }
    new Dygraph(
      this.$el,
      api_url + "/data/" + this.metric + "?start=" + start + "&end=" + end,
      options
    );
  }
});
