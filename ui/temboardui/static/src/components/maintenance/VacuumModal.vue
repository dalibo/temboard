<script setup>
import daterangepicker from "daterangepicker";
import $ from "jquery";
import moment from "moment";
import { onMounted, ref } from "vue";

const vacuumWhen = ref("now");
const vacuumScheduledTime = ref(moment());

onMounted(() => {
  const options = {
    singleDatePicker: true,
    timePicker: true,
    timePicker24Hour: true,
    timePickerSeconds: false,
  };
  $("#vacuumScheduledTime").daterangepicker(
    $.extend(
      {
        startDate: vacuumScheduledTime.value,
      },
      options,
    ),
    function (start) {
      vacuumScheduledTime.value = start;
    },
  );
});

const emit = defineEmits(["apply"]);
</script>

<template>
  <div
    class="modal fade"
    id="vacuumModal"
    tabindex="-1"
    role="dialog"
    aria-labelledby="vacuumModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="vacuumModalLabel">VACUUM</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form id="vacuumForm">
            <div class="mb-3 row">
              <div class="col-sm-2">Mode</div>
              <div class="col-sm-10">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" id="vacuumModeAnalyze" name="mode" value="analyze" />
                  <label class="form-check-label" for="vacuumModeAnalyze"> ANALYZE </label>
                  <small class="form-text text-body-secondary"> Updates statistics after the vacuum. </small>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" id="vacuumModeFull" name="mode" value="full" />
                  <label class="form-check-label" for="vacuumModeFull"> FULL </label>
                  <small class="form-text text-body-secondary">
                    Can reclaim more space but takes more time and exclusively locks the table.
                    <span class="text-danger">Use with caution!</span>
                  </small>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" id="vacuumModeFreeze" name="mode" value="freeze" />
                  <label class="form-check-label" for="vacuumModeFreeze"> FREEZE </label>
                  <small class="form-text text-body-secondary">
                    Selects aggressive "freezing" of tuples. Equivalent to performing VACUUM with the
                    <em><code>vacuum_freeze_min_age</code></em> parameter set to zero.
                  </small>
                </div>
              </div>
            </div>
            <fieldset class="mb-3">
              <div class="row">
                <legend class="col-form-label col-sm-2 pt-0">When</legend>
                <div class="col-sm-10">
                  <div class="form-check form-check-inline">
                    <input
                      class="form-check-input"
                      type="radio"
                      id="vacuumNow"
                      v-model="vacuumWhen"
                      v-bind:value="'now'"
                      checked
                    />
                    <label class="form-check-label" for="vacuumNow"> Now </label>
                  </div>
                  <div class="form-check form-check-inline">
                    <label class="form-check-label" for="vacuumScheduled">
                      <input
                        class="form-check-input"
                        type="radio"
                        id="vacuumScheduled"
                        v-model="vacuumWhen"
                        v-bind:value="'scheduled'"
                      />
                      Scheduled
                    </label>
                  </div>
                  <div v-show="vacuumWhen == 'scheduled'">
                    <button type="button" id="vacuumScheduledTime" class="btn btn-outline-secondary">
                      <i class="fa fa-clock-o"></i>
                      &nbsp;
                      <span>{{ vacuumScheduledTime.toString() }}</span>
                    </button>
                    <input
                      type="hidden"
                      name="datetime"
                      v-bind:value="vacuumScheduledTime.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')"
                      :disabled="vacuumWhen != 'scheduled'"
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
            id="buttonVacuumApply"
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
