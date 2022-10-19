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
| **waiting_sessions_db** | `5`           | `10`      | Waiting sessions per database

## HTTP API

Summary:

| Action                         | Method | URL
| ------------------------------ | ------ | -----
| `checks` list                  | `GET`  | `/server/<address>/<port>/alerting/checks.json`
| Update `checks`                | `POST` | `/server/<address>/<port>/alerting/checks.json`
| `checks` configuration changes | `GET`  | `/server/<address>/<port>/alerting/check_changes/<check>.json?start=<start>&end=<end>`
| Alerts                         | `GET`  | `/server/<address>/<port>/alerting/alerts.json`
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

[{
    "state_by_key": [{
        "state": "OK", "key": "cpu3"
    }, {
        "state": "OK", "key": "cpu2"
    }, {
        "state": "OK", "key": "cpu1"
    }, {
        "state": "OK", "key": "cpu0"
    }],
    "name": "cpu_core",
    "enabled": true,
    "state": "OK",
    "warning": 50.0,
    "critical": 80.0,
    "description": "CPU usage",
    "value_type": "percent"
}, {
    ...
}]
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
    {
        "datetime": "2017-01-01T00:00:00+02:00",
        "enabled": true,
        "warning": 70,
        "critical": 80,
        "description": "CPU Usage"
    },
    {
        "datetime": "2018-05-02T15:05:35.342568+02:00",
        "enabled": true,
        "warning": 50,
        "critical": 80,
        "description": "CPU Usage"
    },
    {
        "datetime": "2018-05-10T00:00:00+02:00",
        "enabled": true,
        "warning": 50,
        "critical": 80,
        "description": "CPU Usage"
    }
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


### Alerts

List of `alerts` (ie. state changes with a warning or critical state value) according to the time interval defined by `start` and `end` arguments (ISO 8601). If no time interval specified, returns the whole history.

**URL** : `/server/<address>/<port>/alerting/alerts.json?start=<start>&end=<end>`

**Method** : `GET`

**Auth required** : YES

**Data example**

```http
GET /server/192.168.122.21/2345/alerting/alerts.json?start=2017-01-01T00:00:00Z&end=2018-05-10T00:00:00Z
```

#### Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
        "datetime": "2017-01-01T00:01:00+02:00",
        "warning": 50,
        "critical": 70,
        "value": 55,
        "state": "WARNING",
        "description": "CPU Usage",
        "key": "cpu0",
        "check": "cpu_core"
    },
    {
        "datetime": "2017-01-01T00:05:35.342568+02:00",
        "warning": 50,
        "critical": 70,
        "value": 72,
        "state": "CRITICAL",
        "description": "CPU Usage",
        "key": "cpu0",
        "check": "cpu_core"
    }
]
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
  {"value":36, "datetime": "2018-05-14T12:25:39+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu2", "value_type": "percent"},
  {"value":49, "datetime": "2018-05-14T12:14:33+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu1", "value_type": "percent"},
  {"value":50, "datetime": "2018-05-14T12:20:37+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu3", "value_type": "percent"},
  {"value":50, "datetime": "2018-05-14T12:20:37+00:00", "state": "OK", "warning":50, "critical":80, "key": "cpu0", "value_type": "percent"}
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
