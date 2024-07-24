<script setup>
import { Plan } from "pev2";
import "pev2/dist/style.css";
import { ref, watch } from "vue";

import ModalDialog from "../components/ModalDialog.vue";

const plan = ref("");
const query = ref("");

const showPlan = ref(false);
const showModal = ref(null);

function submit() {
  showPlan.value = true;
}
</script>

<template>
  <div class="row">
    <div class="col-12 d-flex justify-content-around align-items-center">
      <h1>Plan vizualiser</h1>
      <a href="" @click.prevent="showModal.show()"> <i class="fa fa-fw fa-info"></i><span>Help</span></a>
    </div>

    <ModalDialog ref="showModal" title="Plan Vizualizer Help">
      <div class="modal-body container pb-3">
        <p>For best results, use <strong>EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON)</strong>.</p>
        <p>
          For more information about Explain, see the
          <a href="https://www.postgresql.org/docs/current/using-explain.html">dedicated</a> postgreSQL documentation.
        </p>
        <p>
          Made with <a href="https://github.com/dalibo/pev2"><b>PEV2</b></a
          >.
        </p>
      </div>
    </ModalDialog>

    <div class="col-sm-7 mx-auto mt-4" v-if="!showPlan">
      <form action="/home" @submit.prevent="submit">
        <div class="text-center mb-3" style="float: right">
          <button type="submit" class="btn btn-success">Submit</button>
        </div>
        <br />
        <div class="mb-3">
          <label for="plan" class="control-label">
            Plan
            <span class="small text-muted">(text or JSON)</span>
          </label>
          <textarea
            class="form-control"
            type="text"
            name="plan"
            id="inputPlan"
            rows="8"
            placeholder="Paste execution plan"
            autofocus
            v-model="plan"
          ></textarea>
        </div>
        <div class="mb-3">
          <label for="query" class="control-label">
            Query
            <span class="small text-muted">(optional)</span>
          </label>
          <textarea
            class="form-control"
            type="password"
            name="query"
            id="inputQuery"
            rows="8"
            placeholder="Paste corresponding SQL query"
            v-model="query"
          ></textarea>
        </div>
      </form>
    </div>
  </div>

  <div id="pev2" v-if="showPlan">
    <Plan :plan-source="plan" :plan-query="query" style="height: 100%"></Plan>
  </div>
</template>

<style scoped>
#pev2 {
  /* -headerbar -title -vertical paddings */
  height: calc(100vh - 35px - 48px - 28px);
}
</style>
