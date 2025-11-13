<template>
  <div class="col-12 col-md-6 col-lg-4">
    <div class="card mt-5">
      <div class="card-header bg-primary text-center">
        <img src="/images/temboard-150x32-w.png" />
      </div>

      <div class="card-body">
        <h5 class="text-center mb-4">Reset your password</h5>

        <Error ref="error" />
        <div v-if="message" class="alert alert-success text-center mt-3">{{ message }}</div>

        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">New password</label>
            <input type="password" class="form-control" v-model="password" :disabled="disabled" required />
          </div>

          <div class="mb-3">
            <label class="form-label">Confirm password</label>
            <input type="password" class="form-control" v-model="confirm" :disabled="disabled" required />
          </div>

          <div class="text-center">
            <button type="submit" class="btn btn-primary w-100" :disabled="waiting">
              <span v-if="waiting"><i class="fa fa-spinner fa-spin"></i> Please wait…</span>
              <span v-else>Reset password</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import $ from "jquery";
import { computed, ref } from "vue";

import Error from "../components/Error.vue";

const props = defineProps({
  token: String,
});

const password = ref("");
const confirm = ref("");
const message = ref(null);
const error = ref(null);
const waiting = ref(false);

function submit() {
  waiting.value = true;
  message.value = null;
  error.value.clear();

  $.ajax({
    url: `/json/reset-password/${props.token}`,
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      password: password.value,
      confirm: confirm.value,
    }),
    success: (data) => {
      message.value = data.message;
      setTimeout(() => {
        window.location.href = "/login?reset=success";
      }, 3000);
    },
    error: (xhr) => {
      error.value.fromXHR(xhr);
    },
    complete: () => {
      waiting.value = false;
    },
  });
}
</script>
