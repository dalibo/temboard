import Vue from 'vue/dist/vue.esm'
import NewInstanceWizard from './components/NewInstanceWizard.vue'

window.app = new Vue({
  el: "#vue-app",
  components: {
    'new-instance-wizard': NewInstanceWizard
  },
  created() {
    this.$nextTick(() => {
      var table = $('#tableInstances').DataTable({
        buttons: [{
          attr: {
            title: "Download inventory as CSV",
            id: "buttonDownload",
            "data-toggle": "tooltip"
          },
          className: "btn-sm mx-1",
          text: `<i class="fa fa-download"></i>`,
          action: function(e, dt, node, config) {
            /*
            * Use temBoard UI API instead of datatable export. UI export includes
            * more data and has reordered column.
            */
            var filter = $("#tableInstances_filter input").val();
            var url = new URLSearchParams({filter});
            window.location.replace("/settings/instances.csv?" + url.toString());
          }
        }],
        stateSave: true
      });

      table.buttons().container().appendTo($("#tableInstances_filter"));
    });
  }
});
