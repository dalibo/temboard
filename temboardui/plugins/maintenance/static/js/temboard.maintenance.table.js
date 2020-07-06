/* global Vue */
$(function() {
  "use strict";

  var getScheduledVacuumsTimeout;
  var getScheduledAnalyzesTimeout;
  var getScheduledReindexesTimeout;

  new Vue({
    el: '#app',
    data: {
      table: {
        indexes: []
      },
      loading: true,
      indexSortCriteria: 'total_bytes',
      indexSortCriterias: {
        name: ['Name'],
        total_bytes: ['Size', 'desc'],
        bloat_ratio: ['Bloat', 'desc']
      },
      vacuumWhen: 'now',
      vacuumScheduledTime: moment(),
      scheduledVacuums: [],
      analyzeWhen: 'now',
      analyzeScheduledTime: moment(),
      scheduledAnalyzes: [],
      reindexWhen: 'now',
      reindexScheduledTime: moment(),
      scheduledReindexes: [],
      reindexElementType: null,
      reindexElementName: null
    },
    computed: {
      indexSortOrder: function() {
        return this.indexSortCriterias[this.indexSortCriteria][1];
      },
      indexesSorted: function() {
        return _.orderBy(this.table.indexes, this.indexSortCriteria, this.indexSortOrder);
      },
      filteredScheduledReindexes: function() {
        return _.filter(this.scheduledReindexes, function(reindex) {
          // only reindexes with defined table
          // others are for indexes
          return reindex.table != null;
        });
      }
    },
    created: function() {
      this.fetchData();
    },
    methods: {
      fetchData: function() {
        getData.call(this);
        getScheduledVacuums.call(this);
        getScheduledAnalyzes.call(this);
        getScheduledReindexes.call(this);
      },
      indexSortBy: indexSortBy,
      doVacuum: doVacuum,
      cancelVacuum: cancelVacuum,
      doAnalyze: doAnalyze,
      cancelAnalyze: cancelAnalyze,
      getLatestVacuum: getLatestX('vacuum'),
      getLatestAnalyze: getLatestX('analyze'),
      doReindex: doReindex,
      cancelReindex: cancelReindex,
      checkSession: checkSession
    }
  });

  function getData() {
    $.ajax({
      url: apiUrl,
      contentType: "application/json",
      success: (function(data) {
        this.table = data;
        this.table.indexes.forEach(function(index) {
          index.bloat_ratio = 0;
          if (index.total_bytes) {
            index.bloat_ratio = parseFloat((100 * (index.bloat_bytes / index.total_bytes)).toFixed(1));
          }
        });
        window.setTimeout(postCreated.bind(this), 1);
      }).bind(this),
      error: onError,
      complete: function() {
        this.loading = false;
      }.bind(this)
    });
  }

  function postCreated() {
    $('pre code.sql').each(function(i, block) {
      hljs.highlightBlock(block);
    });
    var options = {
      singleDatePicker: true,
      timePicker: true,
      timePicker24Hour: true,
      timePickerSeconds: false
    };
    $('#vacuumScheduledTime').daterangepicker($.extend({
      startDate: this.vacuumScheduledTime
    }, options), function(start) {
      this.vacuumScheduledTime = start;
    }.bind(this));
    $('#analyzeScheduledTime').daterangepicker($.extend({
      startDate: this.analyzeScheduledTime
    }, options), function(start) {
      this.analyzeScheduledTime = start;
    }.bind(this));
    $('#reindexScheduledTime').daterangepicker($.extend({
      startDate: this.reindexScheduledTime
    }, options), function(start) {
      this.reindexScheduledTime = start;
    }.bind(this));
    $('[data-toggle="popover"]').popover();
  }

  function getScheduledVacuums() {
    window.clearTimeout(getScheduledVacuumsTimeout);
    var count = this.scheduledVacuums.length;
    $.ajax({
      url: apiUrl + '/vacuum/scheduled',
      contentType: "application/json",
      success: (function(data) {
        this.scheduledVacuums = data;
        // refresh list
        getScheduledVacuumsTimeout = window.setTimeout(function() {
          getScheduledVacuums.call(this);
        }.bind(this), 5000);

        // There are less vacuums than before
        // It may mean that a vacuum is finished
        if (data.length < count) {
          getData.call(this);
        }
      }).bind(this),
      error: onError
    });
  }

  function doVacuum() {

    var fields = $('#vacuumForm').serializeArray();
    var mode = fields.filter(function(field) {
      return field.name == 'mode';
    }).map(function(field) {
      return field.value;
    }).join(',');
    var data = {};
    if (mode) {
      data['mode'] = mode;
    }
    var datetime = fields.filter(function(field) {
      return field.name == 'datetime';
    }).map(function(field) {
      return field.value;
    }).join('');
    if (datetime) {
      data['datetime'] = datetime;
    }
    $.ajax({
      method: 'POST',
      url: apiUrl + '/vacuum',
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      data: JSON.stringify(data),
      contentType: "application/json",
      success: (function(data) {
        getScheduledVacuums.call(this);
      }).bind(this),
      error: onError
    });
  }

  function cancelVacuum(id) {
    if (!checkSession()) {
      return;
    }
    $.ajax({
      method: 'DELETE',
      url: maintenanceBaseUrl + '/vacuum/' + id,
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      contentType: "application/json",
      success: (function(data) {
        getScheduledVacuums.call(this);
      }).bind(this),
      error: onError
    });
  }

  function getScheduledAnalyzes() {
    window.clearTimeout(getScheduledAnalyzesTimeout);
    var count = this.scheduledAnalyzes.length;
    $.ajax({
      url: apiUrl + '/analyze/scheduled',
      contentType: "application/json",
      success: (function(data) {
        this.scheduledAnalyzes = data;
        // refresh list
        getScheduledAnalyzesTimeout = window.setTimeout(function() {
          getScheduledAnalyzes.call(this);
        }.bind(this), 5000);

        // There are less analyzes than before
        // It may mean that a analyze is finished
        if (data.length < count) {
          getData.call(this);
        }
      }).bind(this),
      error: onError
    });
  }

  function doAnalyze() {

    var fields = $('#analyzeForm').serializeArray();
    var mode = fields.filter(function(field) {
      return field.name == 'mode';
    }).map(function(field) {
      return field.value;
    }).join(',');
    var data = {};
    if (mode) {
      data['mode'] = mode;
    }
    var datetime = fields.filter(function(field) {
      return field.name == 'datetime';
    }).map(function(field) {
      return field.value;
    }).join('');
    if (datetime) {
      data['datetime'] = datetime;
    }
    $.ajax({
      method: 'POST',
      url: apiUrl + '/analyze',
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      data: JSON.stringify(data),
      contentType: "application/json",
      success: (function(data) {
        getScheduledAnalyzes.call(this);
      }).bind(this),
      error: onError
    });
  }

  function cancelAnalyze(id) {
    if (!checkSession()) {
      return;
    }
    $.ajax({
      method: 'DELETE',
      url: maintenanceBaseUrl + '/analyze/' + id,
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      contentType: "application/json",
      success: (function(data) {
        getScheduledAnalyzes.call(this);
      }).bind(this),
      error: onError
    });
  }

  function getScheduledReindexes() {
    window.clearTimeout(getScheduledReindexesTimeout);
    var count = this.scheduledReindexes.length;
    $.ajax({
      url: apiUrl + '/reindex/scheduled',
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      contentType: "application/json",
      success: (function(data) {
        this.scheduledReindexes = data;
        // refresh list
        getScheduledReindexesTimeout = window.setTimeout(function() {
          getScheduledReindexes.call(this);
        }.bind(this), 5000);

        // There are less reindexes than before
        // It may mean that a reindex is finished
        if (data.length < count) {
          getData.call(this);
        }
      }).bind(this),
      error: onError
    });
  }

  function doReindex() {

    var fields = $('#reindexForm').serializeArray();
    var data = {};
    var datetime = fields.filter(function(field) {
      return field.name == 'datetime';
    }).map(function(field) {
      return field.value;
    }).join('');
    if (datetime) {
      data['datetime'] = datetime;
    }
    // get the element type (either table or index)
    var elementType = fields.filter(function(field) {
      return field.name == 'elementType';
    }).map(function(field) {
      return field.value;
    }).join('');
    // get the element name
    var element = fields.filter(function(field) {
      return field.name == elementType;
    }).map(function(field) {
      return field.value;
    }).join('');
    $.ajax({
      method: 'POST',
      url: [schemaApiUrl, elementType, element, 'reindex'].join('/'),
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      data: JSON.stringify(data),
      contentType: "application/json",
      success: (function(data) {
        getScheduledReindexes.call(this);
      }).bind(this),
      error: onError
    });
  }

  function cancelReindex(id) {
    if (!checkSession()) {
      return;
    }
    $.ajax({
      method: 'DELETE',
      url: maintenanceBaseUrl + '/reindex/' + id,
      beforeSend: function(xhr){xhr.setRequestHeader('X-Session', xsession);},
      contentType: "application/json",
      success: (function(data) {
        getScheduledReindexes.call(this);
      }).bind(this),
      error: onError
    });
  }

  // x is either 'vacuum' or 'analyze'
  function getLatestX(x) {
    return function() {
      var auto = false;
      var date = null;
      var last_x = this.table['last_' + x];
      var last_autox = this.table['last_auto' + x];
      if (!last_x && last_autox) {
        auto = true;
        date = last_autox;
      } else if (last_x && !last_autox) {
        date = last_x;
      } else {
        auto = last_autox > last_x;
        date = auto ? last_autox : last_x
      }
      return {
        auto: auto,
        date: date
      }
    }
  }

  function indexSortBy(criteria, order) {
    this.indexSortCriteria = criteria;
    this.indexSortOrder = order || 'asc';
  }
});
