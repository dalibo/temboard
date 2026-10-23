<script setup>
import { vBTooltip } from "bootstrap-vue-next";
import "bootstrap-vue-next/dist/bootstrap-vue-next.css";
import "bootstrap-vue-next/dist/bootstrap-vue-next.css";
import $ from "jquery";
import { Plan } from "pev2";
import "pev2/dist/pev2.css";
import { ref } from "vue";

const props = defineProps(["query", "options"]);

const query = ref(props.query);
const plan = ref("");
const error = ref(null);
const loading = ref(false);
const selected = ref(props.options.filter((option) => option.default).map((option) => option.name));

const url = ["/proxy", agent_address, agent_port, "explain"].join("/");

function reset() {
  console.log("hey");
  error.value = null;
  plan.value = null;
}

function doExplain() {
  reset();
  loading.value = true;
  $.ajax({
    url: url,
    method: "POST",
    contentType: "application/json",
    dataType: "json",
    data: JSON.stringify({
      query: query.value,
      options: selected.value,
    }),
  })
    .done((data) => {
      plan.value = data;
    })
    .fail((resp) => {
      error.value = resp.responseJSON.error;
    })
    .always(async () => {
      loading.value = false;
    });
}
</script>

<template>
  <div class="row flex-grow-1" v-if="!plan">
    <div class="col">
      <form @submit.prevent="doExplain">
        <div class="d-flex mb-3 align-items-center">
          <span class="me-3"> Options </span>
          <div class="btn-group" role="group" aria-label="Basic example">
            <button
              v-for="option in options"
              :key="option"
              type="button"
              class="btn btn-outline-secondary btn-sm"
              :class="{ active: selected.includes(option.name) }"
              :aria-pressed="selected.includes(option.name)"
              @click="
                selected = selected.includes(option.name)
                  ? selected.filter((item) => item !== option.name)
                  : [...selected, option.name]
              "
              v-b-tooltip.bottom.body="option.description"
            >
              {{ option.name }}
            </button>
          </div>
          <button type="submit" class="btn btn-success ms-auto" :disabled="loading">
            <i class="fa-solid me-1" :class="loading ? 'fa-spinner fa-spin' : 'fa-sitemap'"></i>
            Explain
          </button>
        </div>
        <div class="mb-3">
          <textarea
            id="query"
            name="query"
            class="form-control"
            v-model="query"
            rows="20"
            placeholder="SQL query to get an execution plan for.&#10;&#10;Example : SELECT * FROM table t WHERE t.a = $1;"
          >
          </textarea>
        </div>
      </form>
      <div class="alert alert-danger" v-if="error">
        An error occured:<br />
        {{ error }}
      </div>
    </div>
  </div>
  <div class="container-fluid flex-grow-1 d-flex flex-column" v-else>
    <div class="row">
      <div class="col mb-2 d-flex">
        <button class="ms-auto btn btn-outline-secondary" @click="reset()">
          <i class="fa-solid fa-arrow-left me-2"></i>Explain other query
        </button>
      </div>
    </div>
    <div class="flex-grow-1 d-flex row">
      <Plan :plan-source="JSON.stringify(plan, false, 2)" :plan-query="query"></Plan>
    </div>
  </div>
</template>
