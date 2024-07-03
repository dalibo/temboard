<script setup>
import { Modal, Popover } from "bootstrap";
import $ from "jquery";
import { onMounted, ref } from "vue";

import Error from "../components/Error.vue";

const props = defineProps(["address", "port"]);

const configurationCategories = ref([]);
const configurationStatus = ref([]);
const configuration = ref([]);

const currentCat = ref("");
const queryFilter = ref("");
const settings = ref(null);

const modalLoading = ref(false);

const error = ref(null);
const contentEl = ref(null);

const resetParamName = ref("");
const resetParamValue = ref("");

let resetModal;

onMounted(() => {
  getCategories();
  resetModal = new Modal(document.getElementById("resetModal"));
});

function getCategories() {
  $.ajax({
    url: `/proxy/${props.address}/${props.port}/pgconf/configuration/categories`,
    type: "GET",
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      configurationCategories.value = data;
      getConfiguration();
    },
    error: function (xhr) {
      showError(xhr);
    },
  });
}

function getConfiguration(closeError = true) {
  if (closeError) {
    clearError();
  }
  let url = `/proxy/${props.address}/${props.port}/pgconf/configuration`;
  let query = {};
  if (currentCat.value == "" && queryFilter.value == "") {
    currentCat.value = configurationCategories.value["categories"][0];
  }
  if (queryFilter.value == "") {
    url += `/category/${quotePlus(currentCat.value)}`;
  } else {
    query = { filter: queryFilter.value };
  }
  $.ajax({
    url: url,
    type: "GET",
    data: query,
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      configuration.value = data;
      getStatus();
    },
    error: function (xhr) {
      showError(xhr);
    },
  });
}

function getStatus() {
  $.ajax({
    url: `/proxy/${props.address}/${props.port}/pgconf/configuration/status`,
    type: "GET",
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      configurationStatus.value = data;
      const popoverTriggerList = contentEl.value.querySelectorAll('[data-bs-toggle="popover"]');
      [...popoverTriggerList].map((el) => new Popover(el));
    },
    error: function (xhr) {
      showError(xhr);
    },
  });
}

function submitForm() {
  const popoverTriggerList = contentEl.value.querySelectorAll('[data-bs-toggle="popover"]');
  const popoverList = [...popoverTriggerList].map((el) => new Popover(el));
  popoverList.forEach((p) => p.dispose());
  const formData = { settings: [] };
  clearError();
  let names = [];
  for (let i = 0; i < settings.value.length; i++) {
    const formElements = settings.value[i].elements;
    for (let j = 0; j < formElements.length; j++) {
      const element = formElements[j];
      if (element.name && !names.includes(element.name)) {
        names.push(element.name);
        let value = element.value;
        if (element.type === "checkbox") {
          value = element.checked ? "on" : "off";
        }
        formData.settings.push({ name: element.name, setting: value });
      }
    }
  }
  $.ajax({
    url: `/proxy/${props.address}/${props.port}/pgconf/configuration`,
    type: "POST",
    data: JSON.stringify(formData),
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {},
    error: function (xhr) {
      showError(xhr);
    },
    complete: function () {
      getConfiguration(false);
      window.scrollTo(0, 0);
    },
  });
}

function quotePlus(str) {
  return encodeURIComponent(str).replace(/%20/g, "+");
}

function generatePopoverContent(row) {
  let content = `Type: <b>${row["vartype"]}</b><br>`;
  if (row["unit"]) {
    content += `Unit:<b>${row["unit"]}</b><br>`;
  }
  if (["integer", "real"].includes(row["vartype"])) {
    content += `Minimum: <b>${row["min_val"]}</b><br>` + `Maximum:<b>${row["max_val"]}</b>`;
  }
  return content;
}

function cancel(settingName, settingBootVal) {
  clearError();
  error.value.clear();
  resetParamName.value = settingName;
  resetParamValue.value = settingBootVal;
  resetModal.show();
}

function modalApiCall() {
  modalLoading.value = true;
  let jsonParams = {
    settings: [{ name: resetParamName.value, setting: resetParamValue.value }],
  };
  $.ajax({
    url: `/proxy/${props.address}/${props.port}/pgconf/configuration`,
    type: "POST",
    data: JSON.stringify(jsonParams),
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      getConfiguration();
      resetModal.hide();
      modalLoading.value = false;
    },
    error: function (xhr) {
      modalLoading.value = false;
      error.value.fromXHR(xhr);
    },
  });
}

function parsedEnumVals(enumString) {
  const trimmed = enumString.replace(/^\{|\}$/g, "");
  return trimmed.split(",");
}

function isSelected(value, setting) {
  // Check if the value matches the setting,
  // considering the case where value might be quoted
  return value === setting || `'${value}'` === setting;
}
</script>
<template>
  <div class="modal fade" id="resetModal" tabindex="-1" role="dialog" aria-labelledby="resetModalLabel">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <Error ref="error"></Error>
        <template v-if="modalLoading">
          <div class="modal-header">
            <h4 class="modal-title">Processing, please wait...</h4>
          </div>
          <div class="modal-body">
            <div class="row">
              <div class="col-4 offset-4">
                <div class="progress">
                  <div class="progress-bar progress-bar-striped" style="width: 100%">Please wait ...</div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </template>
        <template v-else>
          <div class="modal-header">
            <h4 class="modal-title" id="resetModalLabel">Reset parameter:</h4>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" id="resetModalBody">
            <p>
              <b>{{ resetParamName }}</b> to <b>{{ resetParamValue }}</b> ?
            </p>
          </div>
          <div class="modal-footer" id="resetModalFooter">
            <button type="button" class="btn btn-success" id="resetYesButton" @click="modalApiCall()">Yes</button>
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
          </div>
        </template>
      </div>
    </div>
  </div>
  <div class="row" v-if="configurationStatus['restart_pending']">
    <div class="col-12">
      <div id="alert-configuration" class="alert alert-warning alert-dismissible" role="alert">
        <p>The options below will be applied after restart :</p>
        <ul>
          <li v-for="change in configurationStatus['restart_changes']">
            {{ change["name"] }}
            <button
              type="button"
              @click="cancel(change['name'], change['boot_val'])"
              class="btn-cancel btn btn-link btn-sm"
            >
              <span class="fa fa-times" aria-hidden="true"></span> Cancel change
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
  <div class="row mb-3">
    <div class="col-3 me-auto">
      <label class="sr-only" for="selectServer">Search</label>
      <div class="input-group">
        <input
          class="form-control"
          id="inputSearchSettings"
          name="filter"
          placeholder="Find in settings"
          v-model="queryFilter"
        />
        <button
          v-if="queryFilter"
          class="input-group-text"
          id="buttonResetSearch"
          @click="
            queryFilter = '';
            getConfiguration();
          "
        >
          <i class="fa fa-fw fa-times"></i>
        </button>
        <button type="submit" class="input-group-text" id="buttonSearchSettings" @click="getConfiguration()">
          <i class="fa fa-fw fa-search"></i>
        </button>
      </div>
    </div>
    <div class="col-7">
      <label class="sr-only" for="selectConfCat">Category</label>
      <div class="input-group">
        <div class="input-group-text">Category</div>
        <select
          class="form-control"
          id="selectConfCat"
          :disabled="queryFilter != ''"
          @change="getConfiguration()"
          v-model="currentCat"
        >
          <template v-if="!queryFilter">
            <option v-for="cat in configurationCategories['categories']" :value="cat" :selected="cat === currentCat">
              {{ cat }}
            </option>
          </template>
        </select>
      </div>
    </div>
  </div>
  <div class="row" ref="contentEl">
    <div class="col-12">
      <div v-for="settingGroup in configuration" class="card">
        <div class="card-header">{{ settingGroup["category"] }}</div>
        <div class="card-body">
          <form ref="settings" @submit.prevent="submitForm">
            <table class="table table-sm">
              <tbody>
                <tr v-for="settingRow in settingGroup['rows']">
                  <td class="badge-setting">
                    <span class="title-setting">{{ settingRow["name"] }}</span>
                    <p class="text-body-secondary mb-0 small">{{ settingRow["desc"] }}</p>
                  </td>
                  <td class="input-setting">
                    <div v-if="settingRow['vartype'] == 'bool'">
                      <div class="form-check form-switch">
                        <input
                          class="form-check-input"
                          type="checkbox"
                          role="switch"
                          :id="'select' + settingRow['name']"
                          :checked="settingRow['setting'] == 'on'"
                          :name="settingRow['name']"
                        />
                      </div>
                    </div>
                    <select
                      v-else-if="settingRow['vartype'] === 'enum'"
                      class="form-control form-control-sm"
                      :name="settingRow['name']"
                      :id="'select' + settingRow['name']"
                    >
                      <option
                        v-for="v in parsedEnumVals(settingRow['enumvals'])"
                        :key="v"
                        :value="v"
                        :selected="isSelected(v, settingRow['setting'])"
                      >
                        {{ v }}
                      </option>
                    </select>
                    <input
                      v-else
                      data-bs-toggle="popover"
                      data-bs-trigger="hover"
                      data-bs-placement="top"
                      data-bs-html="true"
                      :data-bs-content="generatePopoverContent(settingRow)"
                      type="text"
                      class="form-control form-control-sm"
                      :name="settingRow['name']"
                      :id="'input' + settingRow['name']"
                      :placeholder="settingRow['name']"
                      :value="settingRow['setting'] !== null ? settingRow['setting_raw'] : ''"
                    />
                    <button
                      v-if="settingRow['setting'] != settingRow['boot_val']"
                      type="button"
                      class="btn btn-link"
                      :id="'buttonResetDefault_' + settingRow['name']"
                      data-bs-toggle="popover"
                      data-bs-trigger="hover"
                      data-bs-placement="right"
                      :title="settingRow['name']"
                      data-bs-html="true"
                      :data-bs-content="'Reset to: ' + settingRow['boot_val']"
                      @click="cancel(settingRow['name'], settingRow['boot_val'])"
                    >
                      <span class="fa fa-undo" aria-hidden="true"></span>
                      Reset to default
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="row">
              <div class="col-12 text-center">
                <button type="submit" class="btn btn-sm btn-success">Save and reload configuration</button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.input-setting {
  width: 20%;
}
</style>
