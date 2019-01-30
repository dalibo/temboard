/* global Vue */
$(function() {
  "use strict";

  Vue.component('size-distribution-bar', {
    props: [
      'height',
      'total',
      'cat1',
      'cat1raw',
      'cat1label',
      'cat1bis',
      'cat1bisraw',
      'cat1bislabel',
      'cat2',
      'cat2raw',
      'cat2label',
      'cat2',
      'cat2bis',
      'cat2bisraw',
      'cat2bislabel',
      'cat3',
      'cat3raw',
      'cat3label'
    ],
    //props: ['schema', 'table', 'height'],
    methods: {
      toWidthPercent: function(value, total) {
        return 'width: ' + 100 * value / total + '%';
      },
      popoverContent: function(cat) {
        var ret = this[cat + 'label'] + ': ' + this[cat];
        if (this[cat + 'bis']) {
          ret += '<br>';
          ret += '<small class="d-inline-block text-muted">Bloat: ' + this[cat + 'bis'] + '</small>';
        }
        return ret;
      }
    },
    template: '' +
      '  <div class="progress border rounded-0" :style="\'height: \' + height + \';\'">' +
      '    <div class="progress-bar" role="progressbar" :style="toWidthPercent(cat1raw, total)"' +
      '         data-toggle="popover" data-trigger="hover" data-placement="bottom" data-html="true" :data-content="popoverContent(\'cat1\')">' +
      '      <div class="progress rounded-0">' +
      '        <div class="progress-bar bg-cat1" role="progressbar" :style="toWidthPercent(cat1raw - cat1bisraw, cat1raw)"></div>' +
      '        <div class="progress-bar bg-cat1 progress-bar-striped-small" role="progressbar" :style="toWidthPercent(cat1bisraw, cat1raw)"></div>' +
      '      </div>' +
      '    </div>' +
      '    <div class="progress-bar" role="progressbar" :style="toWidthPercent(cat2raw, total)"' +
      '         data-toggle="popover" data-trigger="hover" data-placement="bottom" data-html="true" :data-content="popoverContent(\'cat2\')">' +
      '      <div class="progress rounded-0">' +
      '        <div class="progress-bar bg-cat2" role="progressbar" :style="toWidthPercent(cat2raw - cat2bisraw, cat2raw)"></div>' +
      '        <div class="progress-bar bg-cat2 progress-bar-striped-small" role="progressbar" :style="toWidthPercent(cat2bisraw, cat2raw)"></div>' +
      '      </div>' +
      '    </div>' +
      '    <div class="progress-bar bg-secondary" role="progressbar" :style="toWidthPercent(cat3raw, total)"' +
      '         data-toggle="popover" data-trigger="hover" data-placement="bottom" :data-content="popoverContent(\'cat3\')">' +
      '    </div>' +
      '  </div>'
  });
});
