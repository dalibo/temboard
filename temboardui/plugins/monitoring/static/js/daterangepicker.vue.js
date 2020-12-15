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
                <input type="text" id="inputFrom" v-model="inputFrom" class="form-control">
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
                <input type="text" id="inputTo" v-model="inputTo" class="form-control">
                <div class="input-group-append" data-role="to-picker">
                  <div class="input-group-text">
                    <i class="fa fa-calendar"></i>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <button class="btn btn-primary" v-on:click.prevent="onApply">Apply</button>
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
          if (!this.rawFrom || !this.rawTo) {
            return;
          }
          return rangeUtils.describeTimeRange({from: this.rawFrom, to: this.rawTo});
        },
        // The raw values (examples: 'now-24h', 'Tue Sep 01 2020 10:16:00 GMT+0200')
        // Interaction with parent component is done with from/to props which
        // are unix timestamps
        rawFrom: null,
        rawTo: null,
        // The values to display in the custom range from and to fields
        // we don't use raw values because we may want to pick/change from and
        // to in the form before applying changes
        inputFrom: null,
        inputTo: null,
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
      onApply: onApply,
      setFromTo: setFromTo,
      notify: notify,
      refresh: refresh
    },
    computed: {
      rawFromTo: function() {
        return '' + this.rawFrom + this.rawTo;
      },
      isRefreshable: function() {
        return this.rawFrom && this.rawFrom.toString().indexOf('now') != -1 ||
          this.rawTo && this.rawTo.toString().indexOf('now') != -1;
      }
    },
    mounted: onMounted,
    template: html,
    watch: {
      rawFromTo: function() {
        // "'' + date" will:
        //  - convert 'date' to unix timestamp (ms) if it's a moment object
        //  - not do anything if date is a string ('now - 24h' for example)
        this.$router.push({ query: _.assign({}, this.$route.query, {
          start: '' + this.rawFrom,
          end: '' + this.rawTo
        })});
        this.inputFrom = this.rawFrom;
        this.inputTo = this.rawTo;
      },
      refreshInterval: refresh,
      $route: function(to, from) {
        // Detect changes in browser history (back button for example)
        if (to.query.start) {
          this.rawFrom = convertTimestampToDate(to.query.start);
        }
        if (to.query.end) {
          this.rawTo = convertTimestampToDate(to.query.end);
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
    this.rawFrom = convertTimestampToDate(start);
    this.rawTo = convertTimestampToDate(end);
    this.notify();

    synchronizePickers.call(this);
  }

  function convertTimestampToDate(date) {
    const timestamp = parseInt(date, 10);
    return _.isFinite(timestamp) ? moment(timestamp) : date;
  }

  function loadRangeShortcut(shortcut) {
    this.rawFrom = shortcut.from;
    this.rawTo = shortcut.to;
    this.isPickerOpen = false;
    this.refresh();
  }

  function showHidePicker() {
    this.isPickerOpen = !this.isPickerOpen;
  }

  function parseInputDate(date) {
    /*
     * Tries to convert a date or string to moment
     * Returns value unchanged if not a valid date
     */
    if (moment.isMoment(date)) {
      return date
    }
    const newDate = moment(new Date(date));
    return newDate.isValid() ? newDate : date;
  }

  function onApply() {
    /*
     * Called when global "apply" button is clicked
     */
    this.isPickerOpen = false;
    this.rawFrom = parseInputDate(this.inputFrom);
    this.rawTo = parseInputDate(this.inputTo);
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
          startDate: dateMath.parse(this.rawFrom)
        }, pickerOptions),
        onPickerApply.bind(this, 'inputFrom')
      );
    }
    // update 'to' date picker only if not currently open
    // and 'to' is updating (ie. contains 'now')
    if (!toPicker || !toPicker.data('daterangepicker').isShowing) {
      toPicker = $(this.$el).find('[data-role=to-picker]').daterangepicker(
        $.extend({
          startDate: dateMath.parse(this.rawTo),
          minDate: dateMath.parse(this.rawFrom)
        }, pickerOptions),
        onPickerApply.bind(this, 'inputTo')
      );
    }
  }

  function setToPickerMinDate() {
    $(this.$el).find('[data-role=to-picker]').daterangepicker(
      $.extend({
        minDate: dateMath.parse(this.inputFrom)
      }, pickerOptions),
      onPickerApply.bind(this, 'inputTo')
    );
  }

  function onPickerApply(targetProperty, date) {
    this[targetProperty] = date;
    if (targetProperty === 'inputFrom') {
      setToPickerMinDate.call(this);
    }
  }

  function refresh() {
    this.notify();
    clearTimeout(refreshTimeoutId);
    if (this.refreshInterval) {
      refreshTimeoutId = window.setTimeout(this.refresh, this.refreshInterval * 1000);
    }
  }

  function setFromTo(from, to) {
    this.rawFrom = from;
    this.rawTo = to;
    this.refresh();
  }

  function notify() {
    this.$emit('update:from', dateMath.parse(this.rawFrom));
    this.$emit('update:to', dateMath.parse(this.rawTo, true));
  }
})();
