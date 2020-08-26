/* eslint-env es6 */
/* global Vue, rangeUtils, dateMath */
(function() {
  var html = `
    <div v-cloak>
      <button class="btn btn-secondary" v-on:click="showHidePicker()">
        <i class="fa fa-clock-o"></i>
        <span v-cloak>{{ rangeString() }}</span>
      </button>
      <div class="row position-absolute bg-light border rounded card-body picker-dropdown-panel m-1 w-100 shadow" v-show="isPickerOpen" v-cloak>
        <div class="col-4">
          <h3>
            Custom range
          </h3>
          <form>
            <div class="form-group">
              <label for="inputFrom">From:</label>
              <div class="input-group">
                <input type="text" id="inputFrom" v-model="editRawFrom" class="form-control">
                <div class="input-group-append" data-role="from-picker">
                  <div class="input-group-text">
                    <i class="fa fa-calendar"></i>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label for="inputTo">To:</label>
              <div class="input-group">
                <input type="text" id="inputTo" v-model="editRawTo" class="form-control">
                <div class="input-group-append" data-role="to-picker">
                  <div class="input-group-text">
                    <i class="fa fa-calendar"></i>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <button class="btn btn-primary" v-on:click.prevent="pickerApply">Apply</button>
            </div>
          </form>
        </div>
        <div class="col-8 pl-4">
          <h3>
            Quick ranges
          </h3>
          <div class="row">
            <ul class="list-unstyled col" v-for="section in ranges">
              <li class="shortcut" v-for="range in section">
                <a href :data-from=range.from :data-to="range.to" v-on:click.prevent="loadRangeShortcut(range)">
                  {{ describeTimeRange(range) }}
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="btn-group">
        <button class="btn btn-secondary" v-on:click="refresh()" :disabled="!isRefreshable">
          <i class="fa fa-refresh"></i>
        </button>
        <button type="button" class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" :disabled="!isRefreshable">
          <span class="text-warning" v-if="isRefreshable">
            {{ intervals[refreshInterval] }}
          </span>
        </button>
        <div class="dropdown-menu dropdown-menu-right" style="min-width: 50px;">
          <a class="dropdown-item" href v-on:click.prevent="refreshInterval = null">Off</a>
          <div class="dropdown-divider"></div>
          <a class="dropdown-item" href v-on:click.prevent="refreshInterval = key" v-for="interval, key in intervals">{{ interval }}</a>
        </div>
      </div>
    </div>`;

  var fromPicker;
  var toPicker;
  var refreshTimeoutId;

  Vue.component('daterangepicker', {
    props: ['from', 'to'],
    data: function() {
      return {
        ranges: rangeUtils.getRelativeTimesList(),
        rangeString: function() {
          if (!this.editRawFrom || !this.editRawTo) {
            return;
          }
          return rangeUtils.describeTimeRange({from: this.editRawFrom, to: this.editRawTo});
        },
        editRawFrom: null,
        editRawTo: null,
        refreshInterval: null,
        intervals: {
          '60': '1m',
          '300': '5m',
          '900': '15m'
        },
        isPickerOpen: false
      };
    },
    methods: {
      loadRangeShortcut: loadRangeShortcut,
      describeTimeRange: rangeUtils.describeTimeRange,
      showHidePicker: showHidePicker,
      pickerApply: pickerApply,
      setFromTo: setFromTo,
      notify: notify,
      refresh: refresh
    },
    computed: {
      rawFromTo: function() {
        return this.editRawFrom, this.editRawTo, new Date();
      },
      isRefreshable: function() {
        return this.editRawFrom && this.editRawFrom.toString().indexOf('now') != -1 ||
          this.editRawTo && this.editRawTo.toString().indexOf('now') != -1;
      }
    },
    mounted: onMounted,
    template: html,
    watch: {
      rawFromTo: function() {
        if (this.$route.query.start !== this.editRawFrom || this.$route.query.end !== this.editRawTo) {
          this.$router.push({ query: _.assign({}, this.$route.query, {
            start: '' + this.editRawFrom,
            end: '' + this.editRawTo
          })});
        }
      },
      refreshInterval: refresh,
      $route: function(to, from) {
        if (to.query.start) {
          this.editRawFrom = convertDate(to.query.start);
        }
        if (to.query.end) {
          this.editRawTo = convertDate(to.query.end);
        }
        this.refresh();
      }
    }
  });

  function onMounted() {
    /**
     * Parse location to get start and end date
     * If dates are not provided, falls back to the date range corresponding to
     * the last 24 hours.
     */
    var start = this.$route.query.start || this.from || 'now-24h';
    var end = this.$route.query.end || this.to || 'now';
    this.editRawFrom = convertDate(start);
    this.editRawTo = convertDate(end);
    this.notify();

    synchronizePickers.call(this);
  }

  function convertDate(date) {
    return dateMath.parse(date).isValid() ? date : moment(parseInt(date, 10))
  }

  function loadRangeShortcut(shortcut) {
    this.editRawFrom = shortcut.from;
    this.editRawTo = shortcut.to;
    this.isPickerOpen = false;
    this.refresh();
  }

  function showHidePicker() {
    this.isPickerOpen = !this.isPickerOpen;
  }

  function pickerApply() {
    this.isPickerOpen = false;
    this.refresh();
  }

  var pickerOptions = {
    singleDatePicker: true,
    timePicker: true,
    timePicker24Hour: true,
    timePickerSeconds: false
  };

  /*
   * Make sure that date pickers are up-to-date
   * especially with any 'now-like' dates
   */
  function synchronizePickers() {
    // update 'from' date picker only if not currently open
    // and 'from' is updating (ie. contains 'now')
    if (!fromPicker || !fromPicker.data('daterangepicker').isShowing) {
      fromPicker = $(this.$el).find('[data-role=from-picker]').daterangepicker(
        $.extend({
          startDate: dateMath.parse(this.editRawFrom)
        }, pickerOptions),
        onPickerApply.bind(this, 'editRawFrom')
      );
    }
    // update 'to' date picker only if not currently open
    // and 'to' is updating (ie. contains 'now')
    if (!toPicker || !toPicker.data('daterangepicker').isShowing) {
      toPicker = $(this.$el).find('[data-role=to-picker]').daterangepicker(
        $.extend({
          startDate: dateMath.parse(this.editRawTo),
          minDate: dateMath.parse(this.editRawFrom)
        }, pickerOptions),
        onPickerApply.bind(this, 'editRawTo')
      );
    }
  }

  function onPickerApply(targetProperty, date) {
    this[targetProperty] = date;
  }

  function refresh() {
    this.notify();
    clearTimeout(refreshTimeoutId);
    if (this.refreshInterval) {
      refreshTimeoutId = window.setTimeout(this.refresh, this.refreshInterval * 1000);
    }
  }

  function setFromTo(from, to) {
    this.editRawFrom = from;
    this.editRawTo = to;
    this.refresh();
  }

  function notify() {
    this.$emit('update:from', dateMath.parse(this.editRawFrom));
    this.$emit('update:to', dateMath.parse(this.editRawTo));
  }
})();
