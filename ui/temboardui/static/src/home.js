/* global instances, Vue */
import _ from 'lodash'
import Vue from 'vue/dist/vue.esm'
import VueRouter from 'vue-router'

import './fscreen.js'
import InstanceHomeCard from './components/InstanceHomeCard.vue'

Vue.use(VueRouter)


var refreshInterval = 60 * 1000;


window.instancesVue = new Vue({
  el: '#instances',
  router: new VueRouter(),
  components: {
    "instance-home-card": InstanceHomeCard
  },
  data: function() {
    var groupsFilter = [];
    if (this.$route.query.groups) {
      groupsFilter = this.$route.query.groups.split(',');
    }
    return {
      loading: true,
      instances: [],
      search: this.$route.query.q,
      sort: this.$route.query.sort || 'status',
      groups: groups,
      groupsFilter: groupsFilter
    }
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
          return instance.groups.indexOf(group) != -1;
        });
      });
      return groupFiltered;
    }
  },
  mounted: function() {
    this.fetchInstances();
    window.setInterval(function() { this.fetchInstances() }.bind(this), refreshInterval);
  },
  methods: {
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
    getStatusValue: getStatusValue,
    fetchInstances: function() {
      $.ajax('/home/instances').success(data => {
        this.instances = data
        this.loading = false
        this.$nextTick(function() {
          $('[data-toggle="popover"]').popover();
        })
      })
    }
  },
  watch: {
    search: function(newVal) {
      this.$router.replace({ query: _.assign({}, this.$route.query, {q: newVal })} );
    },
    sort: function(newVal) {
      this.$router.replace({ query: _.assign({}, this.$route.query, {sort: newVal })} );
    },
    groupsFilter: function(newVal) {
      this.$router.replace({ query: _.assign({}, this.$route.query, {groups: newVal.join(',') })} );
    }
  }
});

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

function getChecksCount(instance) {
  var count = _.countBy(
    instance.checks.map(
      function(state) { return state.state; }
    )
  );
  return count;
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
