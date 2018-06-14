/* eslint-env es6 */
/* global Vue, rangeUtils, dateMath */
(function() {
  var html = `
    <div v-cloak>
      <span class="text-muted small" v-if="autoRefresh">auto refresh</span>
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
    </div>`;

  var fromPicker;
  var toPicker;

  Vue.component('daterangepicker', {
    props: ['from', 'to'],
    data: function() {
      return {
        ranges: rangeUtils.getRelativeTimesList(),
        rangeString: function() {
          if (!this.from || !this.to) {
            return;
          }
          return rangeUtils.describeTimeRange({from: this.from, to: this.to});
        },
        editRawFrom: null,
        editRawTo: null,
        isPickerOpen: false
      };
    },
    computed: {
      autoRefresh: function() {
        if (!this.from || !this.to) {
          return;
        }
        return this.from.toString().indexOf('now') != -1 ||
          this.to.toString().indexOf('now') != -1;
      }
    },
    methods: {
      loadRangeShortcut: loadRangeShortcut,
      describeTimeRange: rangeUtils.describeTimeRange,
      showHidePicker: showHidePicker,
      pickerApply: pickerApply
    },
    mounted: synchronizePickers,
    template: html
  });

  function loadRangeShortcut(shortcut) {
    this.editRawFrom = shortcut.from;
    this.editRawTo = shortcut.to;
    this.isPickerOpen = false;
    this.$emit('update', this.editRawFrom, this.editRawTo);
  }

  function showHidePicker() {
    // Make sure input values correspond to current from/to
    // especially when not applying picked dates
    this.editRawFrom = this.from;
    this.editRawTo = this.to;
    this.isPickerOpen = !this.isPickerOpen;
  }

  function pickerApply() {
    this.$emit('update', this.editRawFrom, this.editRawTo);
    this.isPickerOpen = false;
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
})();
