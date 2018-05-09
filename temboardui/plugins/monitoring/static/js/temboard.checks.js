/* global apiUrl, Vue */
$(function() {

  var v = new Vue({
    el: '#checks-container',
    data: {
      checks: null
    },
    methods: {
      getBorderColor: function(state) {
        switch(state) {
        case "WARNING":
          return 'warning';
        case "CRTICAL":
          return 'danger';
        }
      },
      getColor: function(state) {
        switch(state) {
        case "OK":
          return 'success';
        case "WARNING":
          return 'warning';
        case "CRTICAL":
          return 'danger';
        }
      }
    },
    watch: {}
  });

  function refresh() {
    $.ajax({
      url: apiUrl+"/checks.json"
    }).success(function(data) {
      v.checks = data;
    }).error(function(error) {
      console.error(error);
    });
  }

  // refresh every 1 min
  window.setInterval(function() {
    refresh();
  }, 60 * 1000);
  refresh();
});
