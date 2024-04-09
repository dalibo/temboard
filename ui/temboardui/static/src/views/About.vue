<script setup>
import { UseClipboard, UseTimeAgo } from "@vueuse/components";

const props = defineProps(["infos", "temboard_version"]);

function getMetadata() {
  return document.getElementById("metadata").innerText;
}
</script>

<template>
  <div class="row">
    <div class="col-12" id="content" style="font-size: 130%">
      <div style="max-width: 800px" class="mx-auto w-100 w-md-75">
        <div class="row justify-content-center">
          <img class="m-4 w-50 w-xl-25" src="/images/heron.png" />
        </div>
        <div class="row">
          <div class="col-12 text-center">
            <h1 style="font-size: 3rem; color: #d65a16" class="font-weight-bold">temBoard {{ temboard_version }}</h1>
          </div>
        </div>
        <div style="position: relative">
          <UseClipboard v-slot="{ copy, copied }" :legacy="true">
            <button
              id="buttonCopy"
              class="btn btn-light"
              style="position: absolute; top: 0; right: 0"
              title="Copy to clipboard"
              @click="copy(getMetadata())"
            >
              <i class="fa fa-copy"></i> {{ copied ? "Copied" : "Copy" }}
            </button>
          </UseClipboard>
        </div>
        <div class="row mt-2 m-1">
          <div id="metadata">
            <!-- For copy-paste only -->
            <p style="display: none">About temBoard</p>
            <div v-for="(value, key) in infos" :key="key">
              <p class="mb-1">
                <strong>{{ key }}:</strong>
                <template v-if="key === 'Uptime'">
                  <UseTimeAgo v-slot="{ timeAgo }" :time="value">
                    {{ timeAgo }}
                  </UseTimeAgo>
                </template>
                <template v-else>
                  <span :id="key">{{ value }}</span>
                </template>
              </p>
              <template v-if="key === 'Uptime'"
                ><!-- for copy-paste only -->
                <p style="display: none">
                  <strong>Start time:</strong> <span>({{ value }})</span>
                </p>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
