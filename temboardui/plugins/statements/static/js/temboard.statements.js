/* global Vue */
$(function() {
  "use strict";

  new Vue({
    el: '#app',
    data: {
      statements: [],
      sortBy: 'total_time',
      filter: ''
    },
    computed: {
      fields: getFields
    },
    created: function() {
      this.fetchData();
    },
    methods: {
      fetchData: fetchData
    }
  });

  function fetchData() {
    $.ajax({
      url: apiUrl,
      contentType: "application/json",
      success: (function(data) {
        this.statements = data.data;
        window.setTimeout(postCreated, 1);
      }).bind(this)
    });
  }

  function getFields() {
    return [{
      key: 'username',
      label: 'User',
      sortable: true
    }, {
      key: 'dbname',
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
});
