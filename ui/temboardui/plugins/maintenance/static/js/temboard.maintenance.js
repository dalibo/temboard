/* global Vue */
$(function() {
  "use strict";

  new Vue({
    el: '#app',
    data: {
      instance: {},
      databases: [],
      sortCriteria: 'total_bytes',
      sortCriterias: {
        name: ['Name'],
        total_bytes: ['Database Size', 'desc'],
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
      databasesSorted: function() {
        return _.orderBy(this.databases, this.sortCriteria, this.sortOrder);
      }
    },
    methods: {
      fetchData: getInstanceData,
      sortBy: sortBy
    }
  });

  function getInstanceData() {
    $.ajax({
      url: apiUrl,
      contentType: "application/json",
      success: (function(data) {
        this.instance = data.instance;
        this.databases = data.databases;

        this.databases.forEach(function(database) {
          database.tables_bloat_ratio = 0;
          if (database.tables_bytes) {
            database.tables_bloat_ratio = parseFloat((100 * (database.tables_bloat_bytes / database.tables_bytes)).toFixed(1));
          }
          database.indexes_bloat_ratio = 0;
          if (database.indexes_bytes) {
            database.indexes_bloat_ratio = parseFloat((100 * (database.indexes_bloat_bytes / database.indexes_bytes)).toFixed(1));
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
    $('[data-toggle="popover"]').popover();
  }

  function sortBy(criteria, order) {
    this.sortCriteria = criteria;
    this.sortOrder = order || 'asc';
  }
});
