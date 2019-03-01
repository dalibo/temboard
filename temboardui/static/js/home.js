/* eslint-env es6 */
/* global instances, Vue, VueRouter, Dygraph, moment, _, getParameterByName */
$(function() {

  var refreshInterval = 60 * 1000;

  Vue.component('sparkline', {
    props: ['instance', 'metric', 'update'],
    mounted: createChart,
    watch: {
      instance: createChart,
      update: createChart
    },
    template: '<div></div>'
  });

  Vue.component('checks', {
    props: ['instance'],
    computed: {
      checks: function() {
        return getChecksCount(this.instance);
      }
    },
    methods: {
      popoverContent: function(instance) {
        // don't show OK states
        var filtered = instance.checks.filter(function(check) {
          return check.state != 'OK';
        });
        var levels = ['CRITICAL', 'WARNING', 'UNDEF'];
        // make sure we have higher levels checks first
        var ordered = _.sortBy(filtered, function(check) {
          return levels.indexOf(check.state);
        });
        var checksList = ordered.map(function(check) {
          return '<span class="badge badge-' + check.state.toLowerCase() + '">' + check.description + '</span>';
        });
        return checksList.join('<br>');
      }
    },
    template: `
    <div
        class="d-inline-block"
        data-toggle="popover"
        :data-content="popoverContent(instance)"
        data-trigger="hover"
        data-placement="bottom"
        data-container="body"
        data-html="true">
      <span class="badge badge-critical" v-if="checks.CRITICAL">
        CRITICAL: {{ checks.CRITICAL }}</span>
      <span class="badge badge-warning" v-if="checks.WARNING">
        WARNING: {{ checks.WARNING }}</span>
      <span class="badge badge-undef" v-if="checks.UNDEF">
        UNDEF: {{ checks.UNDEF }}</span>
      <span class="badge badge-ok" v-if="!checks.WARNING && !checks.CRITICAL && !checks.UNDEF && checks.OK">OK</span>
    </div>
    `
  });

  $.each(instances, function(index, instance) {
    instance.available = null;
    instance.checks = [];
    instance.loading = true;
  });

  var instancesVue = new Vue({
    el: '#instances',
    router: new VueRouter(),
    data: function() {
      try {
        var groupsFilter = this.$route.query.groups.split(',');
      } catch (e) {
        var groupsFilter = [];
      }
      return {
        instances: instances,
        search: this.$route.query.q,
        sort: this.$route.query.sort || 'status',
        groups: groups,
        groupsFilter: groupsFilter,
        // Property updated in order to refresh charts and checks
        update: moment()
      }
    },
    methods: {
      hasMonitoring: function(instance) {
        var plugins = instance.plugins.map(function(plugin) {
          return plugin.plugin_name;
        });
        return plugins.indexOf('monitoring') != -1;
      },
      toggleGroupFilter: function(group, e) {
        e.preventDefault();
        var index = this.groupsFilter.indexOf(group);
        if (index != -1) {
          this.groupsFilter.splice(index, 1);
        } else {
          this.groupsFilter.push(group);
        }
      },
      changeSort: function(sort, e) {
        e.preventDefault();
        this.sort = sort;
      },
      getStatusValue: getStatusValue
    },
    computed: {
      filteredInstances: function() {
        var self = this;
        var searchRegex = new RegExp(self.search, 'i');
        var filtered = this.instances.filter(function(instance) {
          return searchRegex.test(instance.hostname) ||
                 searchRegex.test(instance.agent_address) ||
                 searchRegex.test(instance.pg_data) ||
                 searchRegex.test(instance.pg_port) ||
                 searchRegex.test(instance.pg_version);
        });
        var sorted;
        if (this.sort == 'status') {
          sorted = sortByStatus(filtered);
        } else {
          sorted = _.sortBy(filtered, this.sort, 'asc');
        }

        var groupFiltered = sorted.filter((instance) => {
          if (!this.groupsFilter.length) {
            return true;
          }
          return this.groupsFilter.every((group) => {
            var instance_groups = instance.groups.map((g) => g.group_name);
            return instance_groups.indexOf(group) != -1;
          });
        });
        return groupFiltered;
      }
    },
    mounted: loadChecks,
    watch: {
      search: function(newVal) {
        this.$router.replace({ query: _.assign({}, this.$route.query, {q: newVal })} );
      },
      sort: function(newVal) {
        this.$router.replace({ query: _.assign({}, this.$route.query, {sort: newVal })} );
      },
      groupsFilter: function(newVal) {
        this.$router.replace({ query: _.assign({}, this.$route.query, {groups: newVal.join(',') })} );
      },
      update: loadChecks,
    }
  });

  checkAvailability();
  window.setInterval(function() {
    instancesVue.update = moment();
    checkAvailability();
  }, refreshInterval);

  function sortByStatus(items) {
    return items.sort(function(a, b) {
      return getStatusValue(b) - getStatusValue(a);
    });
  }

  /*
   * Util to compute a global status value given an instance
   */
  function getStatusValue(instance) {
    var checks = getChecksCount(instance);
    var value = 0;
    if (checks.CRITICAL) {
      value += checks.CRITICAL * 1000000;
    }
    if (checks.WARNING) {
      value += checks.WARNING* 1000;
    }
    if (checks.UNDEF) {
      value += checks.UNDEF;
    }
    return value;
  }

  function createChart() {
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

  var firstLoad = true;
  function loadChecks() {
    // remove any shown popover
    $('[data-toggle="popover"]').popover('hide');
    $.each(this.instances, function(index, instance) {
      instance.loading = true;
      var url = ['/server', instance.agent_address, instance.agent_port, 'alerting/checks.json'].join('/');
      $.ajax(url).success(function(data) {
        instance.checks = data;
        instance.loading = false;
        window.setTimeout(function() {
          $('[data-toggle="popover"]').popover();
          // We hide any tooltip here, since doing it earlier may leave some
          // tooltips shown
          $('[data-toggle="tooltip"]').tooltip('hide');
          $('[data-toggle="tooltip"]').tooltip();
        }, 1);
      }.bind(this));
    });
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

  function checkAvailability() {
    instances.forEach(function(instance) {
      var api_url = ['/server', instance.agent_address, instance.agent_port, 'monitoring'].join('/');
      $.ajax(api_url + '/availability')
      .success(function(data) {
        instance.available = data.available;
      });
    });
  }


  function getChecksCount(instance) {
    return _.countBy(instance.checks.map(function(check) { return check.state; }));
  }

  $('.fullscreen').on('click', function(e) {
    e.preventDefault();
    $(this).addClass('d-none');
    const el = $(this).parents('.container-fluid')[0]
    fscreen.requestFullscreen(el);
  });

  fscreen.onfullscreenchange = function onFullScreenChange(event) {
    if (!fscreen.fullscreenElement) {
      $('.fullscreen').removeClass('d-none');
    }
  }

  // hide fullscreen button if not supported
  $('.fullscreen').toggleClass('d-none', !fscreen.fullscreenEnabled);
});
