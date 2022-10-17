<script type="text/javascript">
  // Global: clearError, showError
  import _ from 'lodash'

  import InstanceCard from './InstanceCard.vue'

  var refreshInterval = 60 * 1000;

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

  export default {
    components: {
      'instance-card': InstanceCard
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
    props: [
      'isAdmin'  // Whether connection user is Admin.
    ],
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
      this.$nextTick(function() {
        this.fetchInstances()
        window.setInterval(function() { this.fetchInstances() }.bind(this), refreshInterval)
        $("[data-toggle=tooltip]", this.$el).tooltip()
      })
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
        clearError()
        $.ajax('/home/instances').success(data => {
          this.instances = data
          this.loading = false
          this.$nextTick(function() {
            $('[data-toggle="popover"]').popover();
          })
        }).fail(xhr => {
          showError(xhr)
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
  }
</script>

<template>
  <div>
    <div class="row">
      <div class="col mb-2">
        <form class="form-inline" onsubmit="event.preventDefault();">
          <input type="text" class="form-control mr-sm-2" placeholder="Search instances" v-model="search">
          <div class="dropdown mr-sm-2">
            <button type="button" class="btn btn-secondary dropdown-toggle"
              data-toggle="dropdown">
              Sort by: <strong v-cloak>{{sort}}</strong>
              <span class="caret"></span>
            </button>
            <div class="dropdown-menu" role="menu">
              <a class="dropdown-item" href v-on:click="changeSort('hostname', $event)">
                <i v-bind:class="['fa fa-fw', {'fa-check': sort == 'hostname'}]"></i>
                Hostname
              </a>
              <a class="dropdown-item" href v-on:click="changeSort('status', $event)">
                <i v-bind:class="['fa fa-fw', {'fa-check': sort == 'status'}]"></i>
                Status
              </a>
            </div>
          </div>
          <div class="dropdown" v-if="groups.length > 1">
            <button type="button" class="btn btn-secondary dropdown-toggle"
              data-toggle="dropdown">
              Groups ({{ groupsFilter.length || 'all' }})
              <span class="caret"></span>
            </button>
            <div class="dropdown-menu" role="menu">
              <a class="dropdown-item" href="#" v-for="group in groups" v-on:click="toggleGroupFilter(group, $event)">
                <i v-bind:class="['fa fa-fw', {'fa-check': groupsFilter.indexOf(group) != -1 }]"></i>
                {{ group }}
              </a>
            </div>
          </div>
        </form>
      </div>
      <div class="col text-center" v-if="groups.length === 1">
        <span class="lead" v-bind:title="'Showing instances of group ' + groups[0]" data-toggle="tooltip">{{ groups[0] }}</span>
      </div>
      <div class="col">
        <p class="text-secondary text-right mt-2 mb-0 mr-4">Refreshed every 1m.</p>
      </div>
    </div>

    <div class="row instance-list">
      <div
        v-for="instance, instanceIndex in filteredInstances"
        :key="instance.hostname + instance.pg_port"
        v-cloak
        class="col-xs-12 col-sm-6 col-md-4 col-lg-3 col-xl-2 pb-3">
        <instance-card
          v-bind:instance="instance"
          v-bind:status_value="getStatusValue(instance)"
          v-bind:index="instanceIndex"
        ></instance-card>
      </div>
    </div>
    <div v-if="!loading && instances.length == 0" class="row justify-content-center" v-cloak>
      <div class="col col-12 col-sm-10 col-md-6 col-lg-4 text-muted text-center">
          <h4 class="m-4">No instance</h4>
          <template v-if="isAdmin">
            <p>No instance is available yet.</p>
            <p>Go to <strong><a href="/settings/instances">Settings</a></strong> to add or configure instances.</p>
          </template>
          <template v-if="!isAdmin">
            <p>You don't have access to any instance.</p>
            <p>Please contact an administrator.</p>
          </template>
      </div>
    </div>
  </div>
</template>
