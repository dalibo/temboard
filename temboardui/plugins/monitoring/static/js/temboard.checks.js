/* global apiUrl, Vue, _ */
$(function() {

  var v = new Vue({
    el: '#checks-container',
    data: {
      checks: null
    },
    methods: {
      getBorderColor: function(state) {
        if (state != 'OK' && state != 'UNDEF') {
          return state.toLowerCase();
        }
      },
      sorted: function(items, key) {
        return _.orderBy(items, key);
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
