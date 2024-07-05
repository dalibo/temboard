<script setup>
import $ from "jquery";
import { onMounted, ref } from "vue";

import Error from "../components/Error.vue";

const props = defineProps(["current_cat", "error_message", "error_code", "query_filter", "address", "port"]);

const data = window.data;
const configurationCategories = data["configuration_categories"];
const configurationStatus = data["configuration_status"];
const configuration = data["configuration"];

const modalLoading = ref(false);

const error = ref(null);

const resetParamName = ref("");
const resetParamValue = ref("");

onMounted(() => {
  if (props.error_code != 0) {
    showError(props.error_message);
  }
});

function generatePopoverContent(row) {
  let content = `<table><tr><td>Type:</td><td><b>${row["vartype"]}</b></td></tr>`;
  if (row["unit"]) {
    content += `<tr><td>Unit:</td><td><b>${row["unit"]}</b></td></tr>`;
  }
  if (["integer", "real"].includes(row["vartype"])) {
    content +=
      `<tr><td>Minimum:</td><td><b>${row["min_val"]}</b></td></tr>` +
      `<tr><td>Maximum:</td><td><b>${row["max_val"]}</b></td></tr>`;
  }
  content += `</table>`;
  return content;
}

function parsedEnumVals(enumString) {
  let trimmed = enumString.replace(/^\{|\}$/g, "");
  return trimmed.split(",");
}

function isSelected(value, setting) {
  // Check if the value matches the setting,
  // considering the case where value might be quoted
  return value === setting || `'${value}'` === setting;
}

function updateHiddenInput(settingName) {
  const isChecked = $("#select" + settingName).is(":checked");
  $("#hidden" + settingName).val(isChecked ? "on" : "off");
}

function cancel(settingName, settingBootVal) {
  error.value.clear();
  resetParamName.value = settingName;
  resetParamValue.value = settingBootVal;
  $("#resetModal").modal("show");
  $("[data-toggle=popover]").popover("hide");
}

function quotePlus(str) {
  return encodeURIComponent(str).replace(/%20/g, "+");
}

function showCat(event) {
  event.preventDefault();
  window.location.replace(event.target.value);
}

function modalApiCall() {
  modalLoading.value = true;
  let jsonParams = {
    settings: [{ name: resetParamName.value, setting: resetParamValue.value }],
  };
  $.ajax({
    url: "/proxy/" + props.address + "/" + props.port + "/pgconf/configuration",
    type: "POST",
    data: JSON.stringify(jsonParams),
    async: true,
    contentType: "application/json",
    dataType: "json",
    success: function (data) {
      var url = window.location.href;
      window.location.replace(url);
    },
    error: function (xhr) {
      modalLoading.value = false;
      error.value.fromXHR(xhr);
    },
  });
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
            <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Close</button>
          </div>
        </template>
        <template v-else>
          <div class="modal-header">
            <h4 class="modal-title" id="resetModalLabel">Reset parameter:</h4>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body" id="resetModalBody">
            <p>
              <b>{{ resetParamName }}</b> to <b>{{ resetParamValue }}</b> ?
            </p>
          </div>
          <div class="modal-footer" id="resetModalFooter">
            <button type="button" class="btn btn-success" id="resetYesButton" @click="modalApiCall()">Yes</button>
            <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancel</button>
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
  <div class="row form-group">
    <div class="col-3 mr-auto">
      <form
        method="get"
        :action="'/server/' + address + '/' + port + '/pgconf/configuration'"
        class="form"
        role="search"
      >
        <label class="sr-only" for="selectServer">Search</label>
        <div class="input-group">
          <input
            class="form-control"
            id="inputSearchSettings"
            name="filter"
            placeholder="Find in settings"
            :value="query_filter"
          />
          <span class="input-group-append">
            <a
              v-if="query_filter"
              class="btn btn-outline-secondary"
              id="buttonResetSearch"
              :href="'/server/' + address + '/' + port + '/pgconf/configuration'"
            >
              <i class="fa fa-fw fa-times"></i>
            </a>
            <button type="submit" class="btn btn-outline-secondary" id="buttonSearchSettings">
              <i class="fa fa-fw fa-search"></i>
            </button>
          </span>
        </div>
      </form>
    </div>
    <div class="col-7">
      <label class="sr-only" for="selectConfCat">Category</label>
      <div class="input-group">
        <div class="input-group-prepend">
          <div class="input-group-text">Category</div>
        </div>
        <select class="form-control" id="selectConfCat" :disabled="query_filter != ''" @change="showCat($event)">
          <template v-if="!query_filter">
            <option
              v-for="cat in configurationCategories['categories']"
              :value="'/server/' + address + '/' + port + '/pgconf/configuration/category/' + quotePlus(cat)"
              :selected="cat === current_cat"
            >
              {{ cat }}
            </option>
          </template>
        </select>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-12">
      <div v-for="settingGroup in configuration" class="card">
        <div class="card-header">{{ settingGroup["category"] }}</div>
        <div class="card-body">
          <form role="form" method="post">
            <table class="table table-sm">
              <tr v-for="settingRow in settingGroup['rows']">
                <td class="badge-setting">
                  <span class="title-setting">{{ settingRow["name"] }}</span>
                  <p class="text-muted mb-0 small">{{ settingRow["desc"] }}</p>
                </td>
                <td class="input-setting">
                  <div v-if="settingRow['vartype'] == 'bool'" class="text-center">
                    <input
                      type="checkbox"
                      :id="'select' + settingRow['name']"
                      :checked="settingRow['setting'] == 'on'"
                      @change="updateHiddenInput(settingRow['name'])"
                    />
                    <input
                      :id="'hidden' + settingRow['name']"
                      type="hidden"
                      :name="settingRow['name']"
                      :value="settingRow['setting']"
                    />
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
                    data-toggle="popover"
                    data-trigger="hover"
                    data-placement="top"
                    data-html="true"
                    :data-content="generatePopoverContent(settingRow)"
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
                    data-toggle="popover"
                    data-trigger="hover"
                    data-placement="right"
                    :title="settingRow['name']"
                    data-html="true"
                    :data-content="'Reset to: ' + settingRow['boot_val']"
                    @click="cancel(settingRow['name'], settingRow['boot_val'])"
                  >
                    <span class="fa fa-undo" aria-hidden="true"></span>
                    Reset to default
                  </button>
                </td>
              </tr>
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
