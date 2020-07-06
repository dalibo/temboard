/* global Vue */
$(function() {
  "use strict";

  var refreshTimeoutId;
  var refreshInterval = 60 * 1000;

  var v = new Vue({
    el: '#app',
    router: new VueRouter(),
    data: {
      statements: [],
      sortBy: 'total_time',
      filter: '',
      from: null,
      to: null
    },
    computed: {
      fields: getFields,
      fromTo: function() {
        return this.from, this.to, new Date();
      }
    },
    methods: {
      fetchData: fetchData,
      onPickerUpdate: onPickerUpdate
    },
    watch: {
      fromTo: function() {
        this.$router.replace({ query: _.assign({}, this.$route.query, {
          start: '' + v.from,
          end: '' + v.to
        })});
        this.fetchData();
      },
    }
  });

  var start = v.$route.query.start || 'now-24h';
  var end = v.$route.query.end || 'now';
  v.from = start;
  v.to = end;

  function fetchData() {
    var startDate = dateMath.parse(this.from);
    var endDate = dateMath.parse(this.to, true);

    $.ajax({
      url: apiUrl,
      data: {
        start: timestampToIsoDate(startDate),
        end: timestampToIsoDate(endDate),
        noerror: 1
      },
      contentType: "application/json",
      success: (function(data) {
        this.statements = data.data;
        window.setTimeout(postCreated, 1);

        window.clearTimeout(refreshTimeoutId);
        if (this.from.toString().indexOf('now') != -1 ||
            this.to.toString().indexOf('now') != -1) {
          refreshTimeoutId = window.setTimeout(fetchData.bind(this), refreshInterval);
        }
      }).bind(this)
    });
  }

  function getFields() {
    return [{
      key: 'rolname',
      label: 'User',
      sortable: true
    }, {
      key: 'datname',
      label: 'DB',
      sortable: true
    }, {
      key: 'query',
      label: 'Query',
      class: 'query',
      sortable: true
    }, {
      key: 'calls',
      label: 'Calls',
      class: 'text-right',
      sortable: true
    }, {
      key: 'total_time',
      label: 'Time',
      formatter: formatDuration,
      class: 'text-right',
      sortable: true
    }, {
      key: 'mean_time',
      label: 'AVG',
      formatter: formatDuration,
      class: 'text-right',
      sortable: true
    }]
  }

  function formatDuration(value) {
    return moment(parseFloat(value, 10)).preciseDiff(moment(0), true);
  }

  function postCreated() {
    $('.sql').each(function(i, block) {
      hljs.highlightBlock(block);
    });
  }

  function onPickerUpdate(from, to) {
    this.from = from;
    this.to = to;
  }

  function timestampToIsoDate(epochMs) {
    var ndate = new Date(epochMs);
    return ndate.toISOString();
  }
});
