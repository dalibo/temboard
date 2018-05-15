# Alerting

temBoard alerting feature intends to trigger visual signals to end users when monitoring data reach defined threshold. This feature is part of `monitoring` plugin.

## Data flow

Monitoring data flow from temBoard agent probes to UI:

1. `agent`: monitoring probes run each 60 seconds, collected data are pushed into local queue (background worker).
2. `agent`: monitoring data picked up from local queue are sent to UI at the URL `/monitoring/collector` (background worker).
3. `UI`: incoming monitoring data are stored, historized (data repository) and aggregated for chart rendering. Some of them are preprocessed before been checked by alerting background worker.
4. `UI`: alerting background worker checks pre-processed monitoring data and stores results into the data repository (background worker).

## Checks

`checks` are what we run against pre-processed monitoring data to verify if something goes wrong. 2 different thresholds are defined for each `check`: `warning` and `critical`. `checks` can be edited by users to change thresholds or disable the `check` itself, these changes are logged. Each set of `checks` is attached to a couple `host_id`, `instance_id`.

Here's the list of current implemented `checks` and default thresholds:

| Name                    | Warning       | Critical  | Description
| ----------------------- | ------------- | --------- | ----------------------------------------------
| **load1**               | `<n_cpu> / 2` | `<n_cpu>` | Loadaverage
| **cpu_core**            | `50`          | `80`      | CPU usage per core/unit (%)
| **memory**              | `50`          | `80`      | Memory usage (%)
| **swap_usage**          | `30`          | `50`      | Swap memory usage (%)
| **fs_usage_mountpoint** | `80`          | `90`      | File systems usage per mount point (%)
| **wal_files_archive**   | `10`          | `20`      | Number of WAL files ready to be archived
| **wal_files_total**     | `50`          | `100`     | Total number of WAL files
| **rollback_db**         | `10`          | `20 `     | Number of rollback'd transactions per database
| **hitreadratio_db**     | `90`          | `80 `     | Hit/read ratio per database (%)
| **sessions_usage**      | `80`          | `90 `     | Client session usage (%)
| **waiting_session_db**  | `5`           | `10`      | Waiting session per database

## HTTP API

Summary:

| Action                         | Method | URL
| ------------------------------ | ------ | -----
| `checks` list                  | `GET`  | `/server/<address>/<port>/alerting/checks.json`
| Update `checks`                | `POST` | `/server/<address>/<port>/alerting/checks.json`
| `checks` configuration changes | `GET`  | `/server/<address>/<port>/alerting/check_changes/<check>.json?start=<start>&end=<end>`
| State overview                 | `GET`  | `/server/<address>/<port>/alerting/overview.json`
| State by `check`               | `GET`  | `/server/<address>/<port>/alerting/show/<check>.json`
| State changes                  | `GET`  | `/server/<address>/<port>/alerting/state_changes/<check>.json?key=<key>&start=<start>&end=<end>`


### `checks` list

Returns the list of attached `checks` and their corresponding current state.

**URL** : `/server/<address>/<port>/alerting/checks.json`

**Method** : `GET`

**Auth required** : YES

#### Success Response

**Code** : `200 OK`

**Content example**

```json
[
  {"name": "cpu_core", "enabled":true, "state": "OK", "warning":50, "critical":80, "description": "CPU usage"},
  {"name": "fs_usage_mountpoint", "enabled":true, "state": "OK", "warning":80, "critical":90, "description": "File systems usage"},
  {"name": "hitreadratio_db", "enabled":true, "state": "OK", "warning":90, "critical":80, "description": "Cache Hit Ratio"},
  {"name": "load1", "enabled":true, "state": "WARNING", "warning":2, "critical":4, "description": "Loadaverage"},
  {"name": "memory", "enabled":true, "state": "OK", "warning":50, "critical":80, "description": "Memory usage"},
  {"name": "rollback_db", "enabled":true, "state": "OK", "warning":10, "critical":20, "description": "Rollbacked transactions"},
  {"name": "sessions_usage", "enabled":true, "state": "OK", "warning":80, "critical":90, "description": "Client sessions"},
  {"name": "swap_usage", "enabled":true, "state": "OK", "warning":30, "critical":50, "description": "Swap usage"},
  {"name": "waiting_session_db", "enabled":true, "state": "OK", "warning":5, "critical":10, "description": "Waiting sessions"},
  {"name": "wal_files_archive", "enabled":true, "state": "OK", "warning":10, "critical":20, "description": "WAL files ready to be archived"},
  {"name": "wal_files_total", "enabled":true, "state": "OK", "warning":50, "critical":100, "description": "WAL files"}
]
```


### Update `checks`

Update one or more `checks`.

**URL** : `/server/<address>/<port>/alerting/checks.json`

**Method** : `POST`

**Auth required** : YES

**Data constraints**

```
{
  "checks":
  [
    {"name": "<check name:string>", "warning": <warning threshold:float>, "critical": <critical threshold:float>, "enabled": <enabled or not:bool>, "description="<check description:string>"},
    ...
  ]
}
```

**Data example**

```json
{
  "checks":
  [
    {"name":"cpu_core","warning":70},
    {"name":"fs_usage_mountpoint","enabled":false}
  ]
}
```

#### Success Response

**Code** : `200 OK`

**Content example**

```json
{}
```

#### Error Response

**Condition** : If 'name' does not match with any existing `check`.

**Code** : `404 NOT FOUND`

**Content** :

```json
{
  "error": "Unknown check 'cpu'"
}
```


### `checks` configuration changes

List of `checks` configuration changes according to the time interval defined by `start` and `end` arguments (ISO 8601). If no time interval specified, returns the whole history.
Each configuration change is materialized as a list of items: `datetime`, `enabled`, `warning`, `critical` and `description`.

**URL** : `/server/<address>/<port>/alerting/check_changes/<check>.json?start=<start>&end=<end>`

**Method** : `GET`

**Auth required** : YES

**Data example**

```http
GET /server/192.168.122.21/2345/alerting/check_changes/cpu_core.json?start=2017-01-01T00:00:00Z&end=2018-05-10T00:00:00Z
```

#### Success Response

**Code** : `200 OK`

**Content example**

```json
[
  ["2018-05-09T15:00:02.451555+02:00", true, 70, 80, "CPU usage"],
  ["2018-05-02T15:05:35.342568+02:00", true, 50, 80, "CPU usage"]
]
```

#### Error Response

**Condition** : If 'name' does not match with any existing `check`.

**Code** : `404 NOT FOUND`

**Content** :

```json
{
  "error": "Unknown check 'cpu'"
}
```


### State by `check`

Gives details (state for each key) about `check`.

**URL** : `/server/<address>/<port>/alerting/states/<check>.json`

**Method** : `GET`

**Auth required** : YES

#### Success Response

**Code** : `200 OK`

**Content example**

```json
[
  {"value":36, "datetime": "2018-05-14T12:25:39+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu2"},
  {"value":49, "datetime": "2018-05-14T12:14:33+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu1"},
  {"value":50, "datetime": "2018-05-14T12:20:37+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu3"},
  {"value":50, "datetime": "2018-05-14T12:20:37+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu0"}
]
```

#### Error Response

**Condition** : If 'name' does not match with any existing `check`.

**Code** : `404 NOT FOUND`

**Content** :

```json
{
  "error": "Unknown check 'cpu'"
}
```


### State changes

List of `checks` state changes according to the time interval defined by `start` and `end` arguments (ISO 8601). If no time interval specified, returns the whole history. The list can be filtered by `key` (arg.).
Each `check` state change is materialized as a list of items: `datetime`, `state`, `key`, `value`, `warning` and `critical`.


**URL** : `/server/<address>/<port>/alerting/state_changes/<check>.json?key=<key>&start=<start>&end=<end>`

**Method** : `GET`

**Auth required** : YES

#### Success Response

**Code** : `200 OK`

**Content example**

```json
[
  ["2018-05-04T11:41:14+02:00", "OK", "cpu0", 8, 50, 80],
  ["2018-05-04T10:51:32+02:00", "CRITICAL", "cpu0", 100, 50, 80],
  ["2018-05-03T20:41:55+02:00", "OK", "cpu0", 3, 50, 80],
  ["2018-05-03T20:40:54+02:00", "WARNING", "cpu0", 59, 50, 80],
  ["2018-05-03T20:37:52+02:00", "CRITICAL", "cpu0", 100, 50, 80],
  ["2018-05-03T17:19:49+02:00", "OK", "cpu0", 20, 50, 80],
  ["2018-05-03T16:57:31+02:00", "CRITICAL", "cpu0", 100, 50, 80],
  ["2018-05-03T16:56:30+02:00", "OK", "cpu0", 21, 50, 80],
  ["2018-05-03T16:55:29+02:00", "WARNING", "cpu0", 57, 50, 80]
]
```

#### Error Response

**Condition** : If 'name' does not match with any existing `check`.

**Code** : `404 NOT FOUND`

**Content** :

```json
{
  "error": "Unknown check 'cpu'"
}
```
