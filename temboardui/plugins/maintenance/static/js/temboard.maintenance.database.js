/* global Vue */
$(function() {
  "use strict";

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
      loading: true
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
      }
    },
    methods: {
      fetchData: getDatabaseData,
      sortBy: sortBy
    }
  });

  function getDatabaseData() {
    $.ajax({
      url: apiUrl,
      contentType: "application/json",
      success: (function(data) {
        this.database = data;
        this.loading = false;

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
      }).bind(this)
    });
  }

  function postCreated() {
    $('[data-toggle="popover"]').popover();
  }

  function sortBy(criteria, order) {
    this.sortCriteria = criteria;
    this.sortOrder = order || 'asc';
  }

});
