<script setup>
import { Plan } from "pev2";
import "pev2/dist/style.css";
import { ref, watch } from "vue";

const plan = ref("");
const query = ref("");

const showPlan = ref(false);

function submit() {
  showPlan.value = true;
}
</script>

<template>
  <div class="row">
    <h1>Plan vizualiser</h1>
    <div class="col-sm-7 mx-auto" v-if="!showPlan">
      <form action="/home" @submit.prevent="submit">
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
            v-model="query"
          ></textarea>
        </div>
        <div class="text-center mb-3">
          <button type="submit" class="btn btn-primary">Submit</button>
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
  height: 700px;
  max-height: calc(100vh - 42px - 92px);
}
</style>
