/* global apiUrl, checkName, Vue, Dygraph, moment */
$(function() {

  var v = new Vue({
    el: '#check-container',
    data: {
      keys: null,
      start: null,
      end: null
    },
    watch: {}
  });

  function refresh() {
    v.start = moment().subtract('2', 'hour');
    v.end = moment();
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
    props: ['check', 'key_', 'start', 'end'],
    data: function() {
      return {
        changes: null
      }
    },
    methods: {
      asPercentStartToFirst: function() {
        if (!this.changes) {
          return 0;
        }
        var firstChange = this.changes[0];
        var total = this.end - this.start;
        var fromStart = moment(firstChange.datetime) - this.start;
        return fromStart / total * 100;
      },
      asPercent: function(index) {
        if (!this.changes) {
          return 0;
        }
        var change = this.changes[index];
        var total = this.end - this.start;
        var next = index != this.changes.length - 1 ? moment(this.changes[index + 1].datetime) : this.end;
        var toNext = next - moment(change.datetime);
        return toNext / total * 100;
      }
    },
    watch: {
      start: loadStateChanges
    },
    mounted: loadStateChanges,
    template: `
      <div>
        <div class="progress">
          <div class="progress-bar bg-light"
              role="progressbar"
              v-bind:style="'width: ' + asPercentStartToFirst() + '%'"
              :aria-valuenow="asPercentStartToFirst()"
              aria-valuemin="0"
              aria-valuemax="100"></div>
          <div v-bind:class="'progress-bar bg-' + change.state.toLowerCase()"
              v-for="(change, index) in changes"
              role="progressbar"
              v-bind:style="'width: ' + asPercent(index) + '%'"
              :aria-valuenow="asPercent(index)"
              aria-valuemin="0"
              aria-valuemax="100"></div>
        </div>
      </div>
    `
  });

  function loadStateChanges() {
    var self = this;
    $.ajax({
      url: apiUrl+"/state_changes/"+ this.check + ".json?key=" + this.key_ + "&start="+timestampToIsoDate(this.start)+"&end="+timestampToIsoDate(this.end)
    }).success(function(data) {
      self.changes = data.reverse();
    }).error(function(error) {

    });
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }
});
