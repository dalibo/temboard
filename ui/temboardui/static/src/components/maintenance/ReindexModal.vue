<script setup>
import daterangepicker from "daterangepicker";
import moment from "moment";
import { onMounted, ref } from "vue";

defineProps(["reindexType", "reindexElementName"]);
const reindexWhen = ref("now");
const reindexScheduledTime = ref(moment());

onMounted(() => {
  const options = {
    singleDatePicker: true,
    timePicker: true,
    timePicker24Hour: true,
    timePickerSeconds: false,
  };
  $("#reindexScheduledTime").daterangepicker(
    $.extend(
      {
        startDate: reindexScheduledTime.value,
      },
      options,
    ),
    function (start) {
      reindexScheduledTime.value = start;
    },
  );
});

const emit = defineEmits(["apply"]);
</script>

<template>
  <div
    class="modal fade"
    id="reindexModal"
    tabindex="-1"
    role="dialog"
    aria-labelledby="reindexModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="reindexModalLabel">reindex</h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <form id="reindexForm">
            <fieldset class="form-group">
              <div class="row">
                <legend class="col-form-label col-sm-2 pt-0">When</legend>
                <div class="col-sm-10">
                  <div class="form-check form-check-inline">
                    <input
                      class="form-check-input"
                      type="radio"
                      id="reindexNow"
                      v-model="reindexWhen"
                      v-bind:value="'now'"
                      checked
                    />
                    <label class="form-check-label" for="reindexNow"> Now </label>
                  </div>
                  <div class="form-check form-check-inline">
                    <label class="form-check-label" for="reindexScheduled">
                      <input
                        class="form-check-input"
                        type="radio"
                        id="reindexScheduled"
                        v-model="reindexWhen"
                        v-bind:value="'scheduled'"
                      />
                      Scheduled
                    </label>
                  </div>
                  <div v-show="reindexWhen == 'scheduled'">
                    <button type="button" id="reindexScheduledTime" class="btn btn-outline-secondary">
                      <i class="fa fa-clock-o"></i>
                      &nbsp;
                      <span>{{ reindexScheduledTime.toString() }}</span>
                    </button>
                    <input
                      type="hidden"
                      name="datetime"
                      v-bind:value="reindexScheduledTime.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')"
                      :disabled="reindexWhen != 'scheduled'"
                    />
                  </div>
                </div>
              </div>
            </fieldset>
            <input type="hidden" name="elementType" :value="reindexType" />
            <input type="hidden" v-bind:name="reindexType" :value="reindexElementName" />
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
          <button
            id="buttonReindexApply"
            type="button"
            class="btn btn-primary"
            v-on:click="emit('apply')"
            data-dismiss="modal"
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
