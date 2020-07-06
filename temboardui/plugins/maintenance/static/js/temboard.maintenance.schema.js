/* global Vue */
$(function() {
  "use strict";

  var getScheduledReindexesTimeout;

  new Vue({
    el: '#app',
    data: {
      schema: {
        tables: [],
        indexes:[]
      },
      sortCriteria: 'total_bytes',
      sortCriterias: {
        name: ['Name'],
        total_bytes: ['Table Size', 'desc'],
        table_bytes: ['Heap Size', 'desc'],
        bloat_ratio: ['Heap Bloat', 'desc'],
        index_bytes: ['Index Size', 'desc'],
        index_bloat_ratio: ['Index Bloat', 'desc'],
        toast_bytes: ['Toast Size', 'desc']
      },
      indexSortCriteria: 'total_bytes',
      indexSortCriterias: {
        name: ['Name'],
        total_bytes: ['Size', 'desc'],
        bloat_ratio: ['Bloat', 'desc']
      },
      loading: true,
      reindexWhen: 'now',
      reindexScheduledTime: moment(),
      scheduledReindexes: [],
      reindexElementType: 'index',
      reindexElementName: null
    },
    computed: {
      sortOrder: function() {
        return this.sortCriterias[this.sortCriteria][1];
      },
      indexSortOrder: function() {
        return this.indexSortCriterias[this.indexSortCriteria][1];
      },
      tablesSorted: function() {
        return _.orderBy(this.schema.tables, this.sortCriteria, this.sortOrder);
      },
      indexesSorted: function() {
        return _.orderBy(this.schema.indexes, this.indexSortCriteria, this.indexSortOrder);
      }
    },
    created: function() {
      this.fetchData();
    },
    methods: {
      fetchData: function() {
        getSchemaData.call(this);
        getScheduledReindexes.call(this);
      },
      sortBy: sortBy,
      indexSortBy: indexSortBy,
      doReindex: doReindex,
      cancelReindex: cancelReindex,
      checkSession: checkSession
    }
  });

  function getSchemaData() {
    $.ajax({
      url: apiUrl,
      contentType: "application/json",
      success: (function(data) {
        this.schema = data;

        this.schema.tables.forEach(function(table) {
          table.bloat_ratio = 0;
          if (table.table_bytes) {
            table.bloat_ratio = parseFloat((100 * (table.bloat_bytes / table.table_bytes)).toFixed(1));
          }
          table.index_bloat_ratio = 0;
          if (table.index_bytes) {
            table.index_bloat_ratio = parseFloat((100 * (table.index_bloat_bytes / table.index_bytes)).toFixed(1));
          }
        });
        this.schema.indexes.forEach(function(index) {
          index.bloat_ratio = 0;
          if (index.total_bytes) {
            index.bloat_ratio = parseFloat((100 * (index.bloat_bytes / index.total_bytes)).toFixed(1));
          }
        });
        window.setTimeout(function() {
          $('pre code.sql').each(function(i, block) {
            hljs.highlightBlock(block);
          });
        }, 1);
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
    $('#reindexScheduledTime').daterangepicker($.extend({
      startDate: this.reindexScheduledTime
    }, options), function(start) {
      this.reindexScheduledTime = start;
    }.bind(this));
    $('[data-toggle="popover"]').popover();
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
          getSchemaData.call(this);
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

  function sortBy(criteria, order) {
    this.sortCriteria = criteria;
    this.sortOrder = order || 'asc';
  }

  function indexSortBy(criteria, order) {
    this.indexSortCriteria = criteria;
    this.indexSortOrder = order || 'asc';
  }
});
