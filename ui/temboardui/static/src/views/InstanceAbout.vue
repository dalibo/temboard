<script setup>
const props = defineProps(["instance_name", "pg_version_summary", "pg_data", "groups", "discover"]);
const settings = ["listen_address", "max_connections", "data_checksums"];
const components = ["psycopg2", "libpq", "bottle", "cyptography"];
let postgres = { cluster_name: "", version: "" };
let system = { distributiion: "" };
let temboard = {};

if (props.discover) {
  postgres = props.discover["postgres"];
  system = props.discover["system"];
  temboard = props.discover["temboard"];
}
</script>
<template>
  <div class="row mx-auto">
    <template v-if="props.discover">
      <div class="text-center mt-4 w-100">
        <h1>
          {{ instance_name }}
          <span class="align-top badge text-bg-secondary">{{ groups[0] }}</span>
        </h1>
        <h3 v-if="groups.length > 1">
          <span v-for="group in groups" class="badge text-bg-secondary">{{ group }}</span>
        </h3>
        <h2 class="text-secondary pb-4 mb-4">{{ pg_version_summary }} serving {{ pg_data }}.</h2>
      </div>
      <table class="table table-sm w-100 mx-auto" style="max-width: 1000px">
        <thead class="thead-light">
          <tr>
            <th colspan="2">
              <h3 class="m-1">
                PostgreSQL <span class="align-middle badge text-bg-secondary">{{ postgres["cluster_name"] }}</span>
              </h3>
            </th>
          </tr>
        </thead>
        <tbody class="postgres">
          <tr>
            <td>Full version</td>
            <td>
              <pre class="version">{{ (postgres["version"] || "Unknown").replace(", ", "\n") }}</pre>
            </td>
          </tr>
          <template v-for="setting in settings">
            <tr v-if="postgres[setting] !== null && postgres[setting] !== undefined">
              <td>
                <tt>{{ setting }}</tt>
              </td>
              <td>
                <template v-if="postgres[setting] === false || postgres[setting] === true">
                  <i class="fa" :class="{ 'fa-check': postgres[setting], 'fa-times': !postgres[setting] }"></i>
                </template>
                <template v-else>
                  {{ postgres[setting] }}
                </template>
              </td>
            </tr>
          </template>
        </tbody>
        <thead class="thead-light">
          <tr>
            <th colspan="2">
              <h3 class="m-1">{{ system["distribution"] ? system["distribution"] : "System" }}</h3>
            </th>
          </tr>
        </thead>
        <tbody class="system">
          <tr v-if="'cpu_model' in system">
            <td>CPU</td>
            <td>
              <tt>{{ system["cpu_count"] }} x {{ system["cpu_model"] }}</tt>
            </td>
          </tr>
          <tr v-if="'memory' in system">
            <td>Memory</td>
            <td>
              <tt>{{ (system["memory"] / 1024 / 1024 / 1024).toFixed(2) }} GiB</tt>
            </td>
          </tr>
          <tr v-if="'swap' in system">
            <td>Swap</td>
            <td>
              <tt>{{ (system["swap"] / 1024 / 1024 / 1024).toFixed(2) }} GiB</tt>
            </td>
          </tr>
          <tr>
            <td>Kernel</td>
            <td>
              <tt>{{ system["os"] ? system["os"] : "Linux" }} {{ system["os_version"] }}</tt>
            </td>
          </tr>
        </tbody>
        <thead class="thead-light">
          <tr>
            <th colspan="2">
              <h3 class="m-1">temBoard Agent {{ temboard["agent_version"] }}</h3>
            </th>
          </tr>
        </thead>
        <tbody class="temboard">
          <tr v-if="'plugins' in temboard">
            <td>Plugins</td>
            <td>
              <ul class="list-inline plugins">
                <li v-for="plugin in temboard['plugins']" :class="'list-inline-item ' + plugin" style="font-size: 135%">
                  <span class="badge text-bg-light">{{ plugin }}</span>
                </li>
              </ul>
            </td>
          </tr>
          <tr v-if="'configfile' in temboard">
            <td>Configuration file</td>
            <td>
              <tt>{{ temboard["configfile"] }}</tt>
            </td>
          </tr>
          <tr v-if="'python_version' in temboard">
            <td>Python {{ temboard["python_version"] }}</td>
            <td>
              <tt>{{ temboard["pythonbin"] }}</tt>
            </td>
          </tr>
          <tr v-for="component in components" v-if="component + '_version' in temboard">
            <td>{{ component }}</td>
            <td>
              <tt>{{ temboard[component + "_version"] }}</tt>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
    <template v-else>
      <div class="text-center mt-4 w-100">
        <h1>
          {{ instance_name }}
          <span class="align-top badge text-bg-secondary">{{ groups[0] }}</span>
        </h1>
      </div>
      <div class="alert alert-warning mx-auto" role="alert">
        <h2><i class="fa fa-warning fa-fw"></i>WARNING</h2>
        <p>Agent never reported details. If this takes more than a few minutes, please investigate in logs.</p>
      </div>
    </template>
  </div>
</template>
