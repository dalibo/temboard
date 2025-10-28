<template>
  <div class="col-12 col-md-6 col-lg-4">
    <div class="card mt-5">
      <div class="card-header bg-primary text-center">
        <a href="/login">
          <img src="/images/temboard-150x32-w.png" />
        </a>
      </div>

      <div class="card-body">
        <h5 class="text-center mb-3">Reset your password</h5>
        <p class="text-muted text-center mb-4">Enter your username or registered email.</p>

        <Error ref="error" />

        <form @submit.prevent="submit">
          <div class="mb-3">
            <label for="inputIdentifier" class="form-label">Username or Email</label>
            <input
              type="text"
              class="form-control"
              id="inputIdentifier"
              v-model="identifier"
              placeholder="Username or Email"
              :disabled="waiting"
              required
            />
          </div>
          <div class="text-center">
            <button type="submit" class="btn btn-primary w-100" :disabled="waiting">
              <span v-if="waiting"><i class="fa fa-spinner fa-spin"></i> Please wait…</span>
              <span v-else>Send password reset link</span>
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

const identifier = ref("");
const error = ref(null);
const waiting = ref(false);

function submit() {
  waiting.value = true;
  error.value.clear();

  $.ajax({
    url: "/json/reset-password",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      identifier: identifier.value,
    }),
    success: () => {
      window.location.href = "/login";
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
