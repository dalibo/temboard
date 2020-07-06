/* global Vue */
$(function() {
  "use strict";

  var getScheduledVacuumsTimeout;
  var getScheduledAnalyzesTimeout;
  var getScheduledReindexesTimeout;

  new Vue({
    el: '#app',
    data: {
      database: {
        schemas: []
      },
      sortCriteria: 'total_bytes',
      sortCriterias: {
        name: ['Name'],
        total_bytes: ['Schemas Size', 'desc'],
        tables_bytes: ['Tables Size', 'desc'],
        tables_bloat_ratio: ['Tables Bloat', 'desc'],
        indexes_bytes: ['Indexes Size', 'desc'],
        indexes_bloat_ratio: ['Indexes Bloat', 'desc'],
        toast_bytes: ['Toast Size', 'desc']
      },
      loading: true,
      vacuumWhen: 'now',
      vacuumScheduledTime: moment(),
      scheduledVacuums: [],
      analyzeWhen: 'now',
      analyzeScheduledTime: moment(),
      scheduledAnalyzes: [],
      reindexWhen: 'now',
      reindexScheduledTime: moment(),
      scheduledReindexes: [],
      reindexElementType: 'database',
      reindexElementName: null
    },
    created: function() {
      this.fetchData();
    },
    computed: {
      sortOrder: function() {
        return this.sortCriterias[this.sortCriteria][1];
      },
      schemasSorted: function() {
        return _.orderBy(this.database.schemas, this.sortCriteria, this.sortOrder);
      },
      filteredScheduledReindexes: function() {
        // don't do anything
        // only relevant for the table view
        return this.scheduledReindexes;
      }
    },
    methods: {
      fetchData: function() {
        getData.call(this);
        getScheduledVacuums.call(this);
        getScheduledAnalyzes.call(this);
        getScheduledReindexes.call(this);
      },
      sortBy: sortBy,
      checkSession: checkSession,
      doVacuum: doVacuum,
      cancelVacuum: cancelVacuum,
      doAnalyze: doAnalyze,
      cancelAnalyze: cancelAnalyze,
      doReindex: doReindex,
      cancelReindex: cancelReindex
    }
  });

  function getData() {
    $.ajax({
      url: apiUrl,
      contentType: "application/json",
      success: (function(data) {
        this.database = data;

        this.database.schemas.forEach(function(schema) {
          schema.tables_bloat_ratio = 0;
          if (schema.tables_bytes) {
            schema.tables_bloat_ratio = parseFloat((100 * (schema.tables_bloat_bytes / schema.tables_bytes)).toFixed(1));
          }
          schema.indexes_bloat_ratio = 0;
          if (schema.indexes_bytes) {
            schema.indexes_bloat_ratio = parseFloat((100 * (schema.indexes_bloat_bytes / schema.indexes_bytes)).toFixed(1));
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

  function sortBy(criteria, order) {
    this.sortCriteria = criteria;
    this.sortOrder = order || 'asc';
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
      onError: onError
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
      onError: onError
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
    $.ajax({
      method: 'POST',
      url: [apiUrl, 'reindex'].join('/'),
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
});
