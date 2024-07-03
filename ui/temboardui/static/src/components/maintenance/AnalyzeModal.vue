<script setup>
import daterangepicker from "daterangepicker";
import $ from "jquery";
import moment from "moment";
import { onMounted, ref } from "vue";

const analyzeWhen = ref("now");
const analyzeScheduledTime = ref(moment());

onMounted(() => {
  const options = {
    singleDatePicker: true,
    timePicker: true,
    timePicker24Hour: true,
    timePickerSeconds: false,
  };
  $("#analyzeScheduledTime").daterangepicker(
    $.extend(
      {
        startDate: analyzeScheduledTime.value,
      },
      options,
    ),
    function (start) {
      analyzeScheduledTime.value = start;
    },
  );
});

const emit = defineEmits(["apply"]);
</script>
<template>
  <div
    class="modal fade"
    id="analyzeModal"
    tabindex="-1"
    role="dialog"
    aria-labelledby="analyzeModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="analyzeModalLabel">ANALYZE</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <form id="analyzeForm">
            <fieldset class="form-group">
              <div class="row">
                <legend class="col-form-label col-sm-2 pt-0">When</legend>
                <div class="col-sm-10">
                  <div class="form-check form-check-inline">
                    <input
                      class="form-check-input"
                      type="radio"
                      id="analyzeNow"
                      v-model="analyzeWhen"
                      v-bind:value="'now'"
                      checked
                    />
                    <label class="form-check-label" for="analyzeNow"> Now </label>
                  </div>
                  <div class="form-check form-check-inline">
                    <label class="form-check-label" for="analyzeScheduled">
                      <input
                        class="form-check-input"
                        type="radio"
                        id="analyzeScheduled"
                        v-model="analyzeWhen"
                        v-bind:value="'scheduled'"
                      />
                      Scheduled
                    </label>
                  </div>
                  <div v-show="analyzeWhen == 'scheduled'">
                    <button type="button" id="analyzeScheduledTime" class="btn btn-outline-secondary">
                      <i class="fa fa-clock-o"></i>
                      &nbsp;
                      <span>{{ analyzeScheduledTime.toString() }}</span>
                    </button>
                    <input
                      type="hidden"
                      name="datetime"
                      v-bind:value="analyzeScheduledTime.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')"
                      :disabled="analyzeWhen != 'scheduled'"
                    />
                  </div>
                </div>
              </div>
            </fieldset>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button
            id="buttonAnalyzeApply"
            type="button"
            class="btn btn-primary"
            v-on:click="emit('apply')"
            data-bs-dismiss="modal"
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
