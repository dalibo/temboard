<script setup>
/* A dialog to warn about an upcoming migration in temboard 9.0. */
import $ from "jquery";

import ModalDialog from "../ModalDialog.vue";

const props = defineProps({
  objectClass: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
});

defineExpose({
  show: function () {
    $(this.$el).modal("show");
  },
});
</script>

<template>
  <ModalDialog id="modalMigrationGroups" :title="title">
    <div class="modal-body">
      <template v-if="objectClass === 'group'">
        <p><b>This group belongs to more than one user group.</b></p>
        <p>
          In temBoard 9.0, we plan to remove the ability to put an instance group in several user groups. Each group of
          instance will be associated to a single user group. To prepare the upgrade, review your configuration to put
          this group in a single user group.
        </p>
      </template>
      <template v-if="objectClass === 'instance'">
        <p><b>This instance belongs to more than one group of instances.</b></p>
        <p>
          In temBoard 9.0, we plan to remove the ability to put an instance in several groups of instances. Each
          instance will be associated to a single group of instances called <em>Environment</em>. To prepare the
          upgrade, review your configuration to put this instance in a single group of instances.
        </p>
        <p>temBoard 9.0 upgrade will create an <em>environment</em> per combination of groups of instance.</p>
      </template>
      <p>
        Read more details and send us feedback on GitHub issue
        <a href="https://github.com/dalibo/temboard/issues/1283">#1283</a>.
      </p>
      <p class="text-start"><em>temBoard development team.</em></p>
    </div>
  </ModalDialog>
</template>
