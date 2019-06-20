import * as _ from 'lodash';
import Vue from 'vue';

require('base');

/* global apiUrl */
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
    }).done(function(data) {
      v.checks = data;
    }).fail(function(error) {
      console.error(error);
    });
  }

  // refresh every 1 min
  window.setInterval(function() {
    refresh();
  }, 60 * 1000);
  refresh();
});
