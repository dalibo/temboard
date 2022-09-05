import Vue from 'vue/dist/vue.esm'
import DeleteInstanceDialog from './components/DeleteInstanceDialog.vue'
import NewInstanceWizard from './components/NewInstanceWizard.vue'
import UpdateInstanceDialog from './components/UpdateInstanceDialog.vue'

window.app = new Vue({
  el: "#vue-app",
  components: {
    'delete-instance-dialog': DeleteInstanceDialog,
    'new-instance-wizard': NewInstanceWizard,
    'update-instance-dialog': UpdateInstanceDialog
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
