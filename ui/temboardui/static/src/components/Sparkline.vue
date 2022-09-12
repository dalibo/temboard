<script type="text/javascript">
  import _ from 'lodash'
  import Dygraph from 'dygraphs'
  import moment from 'moment'

export default {
  props: ['instance', 'metric'],
  mounted: function() {
    this.createChart()
  },
  watch: {
    instance: function() {
      this.createChart()
    }
  },
  methods: {
    createChart: function() {
      var api_url = ['/server', this.instance.agent_address, this.instance.agent_port, 'monitoring'].join('/');

      var start = moment().subtract(1, 'hours');
      var end = moment();
      var defaultOptions = {
        axes: {
          x: {
            drawAxis: false,
            drawGrid: false
          },
          y: {
            drawAxis: false,
            drawGrid: false
          }
        },
        dateWindow: [start, end],
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

      var params = "?start=" + start.toISOString() + "&end=" + end.toISOString();
      var metricsUrl = api_url + "/data/" + this.metric + params;
      var data = null;
      var dataReq = $.get(metricsUrl, function(_data) {
        data = _data;
      });
      // Get the dates when the instance was unavailable
      var unavailabilityData = '';
      var promise = $.when(dataReq);
      var unavailabilityUrl = api_url + '/unavailability' + params;
      if (this.metric == 'tps') {

        promise = $.when(dataReq,
          $.get(unavailabilityUrl, function(_data) { unavailabilityData = _data; })
        );
      }
      promise.then(function() {
        // fill unavailability data with NaN
        var colsCount = data.split('\n')[0].split(',').length;
        var nanArray = new Array(colsCount - 1).fill('NaN');
        nanArray.unshift('');
        unavailabilityData = unavailabilityData.replace(/\n/g, nanArray.join(',') + '\n');

        var chart = new Dygraph(
          this.$el,
          data + unavailabilityData,
          options
        );
        var last;
        if (this.metric == 'tps') {
          var lastCommit = chart.getValue(chart.numRows() - 1, 1);
          var lastRollback = chart.getValue(chart.numRows() - 1, 2);
          last = lastCommit + lastRollback;
        } else {
          last = chart.getValue(chart.numRows() - 1, 1);
        }
        this.instance['current' + _.capitalize(this.metric)] = last;
        instancesVue.$forceUpdate();
      }.bind(this));
    }
  }
}
</script>

<template>
  <div></div>
</template>
