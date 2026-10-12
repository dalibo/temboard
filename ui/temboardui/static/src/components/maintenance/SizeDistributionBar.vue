<script setup>
import { BPopover } from "bootstrap-vue-next";

const props = defineProps([
  "height",
  "total",
  "cat1",
  "cat1raw",
  "cat1label",
  "cat1bis",
  "cat1bisraw",
  "cat1bislabel",
  "cat2",
  "cat2raw",
  "cat2label",
  "cat2",
  "cat2bis",
  "cat2bisraw",
  "cat2bislabel",
  "cat3",
  "cat3raw",
  "cat3label",
]);

function toWidthPercent(value, total) {
  return `width: ${(100 * value) / total}%`;
}

function popoverContent(cat) {
  let ret = `${props[cat + "label"]}: ${props[cat]}`;
  if (props[cat + "bis"]) {
    ret += `<br><small class="d-inline-block text-body-secondary">Bloat: ${props[cat + "bis"]}</small>`;
  }
  return ret;
}
</script>

<template>
  <div class="progress border rounded-0" :style="{ height: props.height + 'px' }">
    <BPopover>
      <template #target>
        <div class="progress-bar" role="progressbar" :style="toWidthPercent(cat1raw, total)">
          <div class="progress rounded-0">
            <div
              class="progress-bar bg-cat1"
              role="progressbar"
              :style="toWidthPercent(cat1raw - cat1bisraw, cat1raw)"
            ></div>
            <div
              class="progress-bar bg-cat1 progress-bar-striped-small"
              role="progressbar"
              :style="toWidthPercent(cat1bisraw, cat1raw)"
            ></div>
          </div>
        </div>
      </template>
      <div v-html="popoverContent('cat1')" />
    </BPopover>
    <BPopover>
      <template #target>
        <div class="progress-bar" role="progressbar" :style="toWidthPercent(cat2raw, total)">
          <div class="progress rounded-0">
            <div
              class="progress-bar bg-cat2"
              role="progressbar"
              :style="toWidthPercent(cat2raw - cat2bisraw, cat2raw)"
            ></div>
            <div
              class="progress-bar bg-cat2 progress-bar-striped-small"
              role="progressbar"
              :style="toWidthPercent(cat2bisraw, cat2raw)"
            ></div>
          </div>
        </div>
      </template>
      <div v-html="popoverContent('cat2')" />
    </BPopover>
    <BPopover>
      <template #target>
        <div class="progress-bar bg-secondary" role="progressbar" :style="toWidthPercent(cat3raw, total)"></div>
      </template>
      <div v-html="popoverContent('cat3')" />
    </BPopover>
  </div>
</template>
