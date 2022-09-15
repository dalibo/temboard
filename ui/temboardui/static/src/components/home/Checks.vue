<script type="text/javascript">
  import _ from 'lodash'

  export default {
    props: ['instance'],
    computed: {
      available: function() {
        return this.instance.available;
      },
      checks: function() {
        var count = _.countBy(
          this.instance.checks.map(
            function(state) { return state.state; }
          )
        );
        return count;
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
    }
  }
</script>

<template>
  <div
    class="d-inline-block"
    data-toggle="popover"
    :data-content="popoverContent(instance)"
    data-trigger="hover"
    data-placement="bottom"
    data-container="body"
    data-html="true">
    <span class="badge badge-critical mr-1" v-if="!available" title="Unable to connect to Postgres">UNAVAILABLE</span>
    <span class="badge badge-critical mr-1" v-if="checks.CRITICAL">
      CRITICAL: {{ checks.CRITICAL }}</span>
    <span class="badge badge-warning mr-1" v-if="checks.WARNING">
      WARNING: {{ checks.WARNING }}</span>
    <span class="badge badge-undef mr-1" v-if="checks.UNDEF">
      UNDEF: {{ checks.UNDEF }}</span>
      <span class="badge badge-ok mr-1" v-if="!checks.WARNING && !checks.CRITICAL && !checks.UNDEF && checks.OK">OK</span>
    </div>
</template>
