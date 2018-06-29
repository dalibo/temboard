/* eslint-env es6 */
/* global instances, Vue, Dygraph, moment, _, getParameterByName */
$(function() {

  var refreshInterval = 60 * 1000;

  Vue.component('sparkline', {
    props: ['instance', 'metric'],
    mounted: createChart,
    template: '<div></div>'
  });

  Vue.component('checks', {
    props: ['instance'],
    data: function() {
      return {
        checks: {}
      };
    },
    mounted: loadChecks,
    template: `
    <div>
    Status:
    <span class="badge badge-ok" v-if="!checks.WARNING && !checks.CRITICAL">OK</span>
    <span class="badge badge-warning" v-if="checks.WARNING">WARNING: {{ checks.WARNING }}</span>
    <span class="badge badge-critical" v-if="checks.CRITICAL">CRITICAL: {{ checks.CRITICAL }}</span>
    </div>
    `
  });

  new Vue({
    el: '#instances',
    data: {
      instances: instances,
      search: ''
    },
    methods: {
      hasMonitoring: function(instance) {
        var plugins = instance.plugins.map(function(plugin) {
          return plugin.plugin_name;
        });
        return plugins.indexOf('monitoring') != -1;
      }
    },
    mounted: function() {
      this.search = getParameterByName('q') || '';
    },
    computed: {
      filteredInstances: function() {
        var self = this;
        var searchRegex = new RegExp(self.search, 'i');
        return this.instances.filter(function(instance) {
          return searchRegex.test(instance.hostname) ||
                 searchRegex.test(instance.agent_address) ||
                 searchRegex.test(instance.pg_data) ||
                 searchRegex.test(instance.pg_port) ||
                 searchRegex.test(instance.pg_version);
        });
      }
    },
    watch: {
      'search': updateQueryParams
    }
  });

  function updateQueryParams() {
    var params = $.param({
      q: this.search
    });
    var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?' + params;
    window.history.replaceState({path: newurl}, '', newurl);
  }

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
        },
        y: {
          axisLabelFontSize: 9,
          axisLabelColor: '#999',
          axisLabelWidth: 20,
          pixelsPerLabel: 10,
          drawAxesAtZero: true,
          includeZero: true,
          axisLineColor: '#dfdfdf',
          gridLineColor: '#dfdfdf',
          axisLabelFormatter: function(d) {
            return abbreviateNumber(d);
          }
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

    // auto refresh
    window.setTimeout(function() {
      createChart.call(this);
    }.bind(this), refreshInterval);
  }

  function loadChecks() {
    var url = ['/server', this.instance.agent_address, this.instance.agent_port, 'alerting/checks.json'].join('/');
    $.ajax(url).success(function(data) {
      this.checks = _.countBy(data.map(function(check) { return check.state; }));
    }.bind(this));

    // auto refresh
    window.setTimeout(function() {
      loadChecks.call(this);
    }.bind(this), refreshInterval);
  }

  function abbreviateNumber(number) {
    var abbrev = [ "k", "m", "b", "t" ];

    for (var i = abbrev.length - 1; i >= 0; i--) {

      var size = Math.pow(10, (i + 1) * 3);

      if(size <= number) {
        number = Math.round(number * 10 / size) / 10;
        if((number == 1000) && (i < abbrev.length - 1)) {
          number = 1;
          i++;
        }
        number += abbrev[i];
        break;
      }
    }

    return number;
  }
});
