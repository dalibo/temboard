define({ "api": [
  {
    "type": "get",
    "url": "/activity",
    "title": "Get the list of backend.",
    "version": "0.0.1",
    "name": "Activity",
    "group": "Activity",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.rows",
            "description": "<p>List of backends.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.pid",
            "description": "<p>Process ID of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.database",
            "description": "<p>Name of the database this backend is connected to.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.user",
            "description": "<p>Name of the user logged into this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.client",
            "description": "<p>IP address of the client connected to this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.cpu",
            "description": "<p>CPU usage (%) of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.memory",
            "description": "<p>Memory usage (%) of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.read_s",
            "description": "<p>Read rate of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.write_s",
            "description": "<p>Write rate of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.iow",
            "description": "<p>Is this backend waiting for IO operations.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.w",
            "description": "<p>Is this backend waiting for lock acquisition.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.duration",
            "description": "<p>Query duration (s).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.state",
            "description": "<p>State of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.query",
            "description": "<p>Query.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"rows\":\n    [\n        {\n            \"pid\": 6285,\n            \"database\": \"postgres\",\n            \"user\": \"postgres\",\n            \"client\": null,\n            \"cpu\": 0.0,\n            \"memory\": 0.13,\n            \"read_s\": \"0.00B\",\n            \"write_s\": \"0.00B\",\n            \"iow\": \"N\",\n            \"wait\": \"N\",\n            \"duration\": \"1.900\",\n            \"state\": \"idle\",\n            \"query\": \"SELECT 1;\"\n        },\n        ...\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/activity",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/activity/__init__.py",
    "groupTitle": "Activity"
  },
  {
    "type": "get",
    "url": "/activity/blocking",
    "title": "Get the list of backend blocking other backends due to lock acquisition.",
    "version": "0.0.1",
    "name": "ActivityBlocking",
    "group": "Activity",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.rows",
            "description": "<p>List of backends.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.pid",
            "description": "<p>Process ID of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.database",
            "description": "<p>Name of the database this backend is connected to.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.user",
            "description": "<p>Name of the user logged into this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.cpu",
            "description": "<p>CPU usage (%) of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.memory",
            "description": "<p>Memory usage (%) of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.read_s",
            "description": "<p>Read rate of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.write_s",
            "description": "<p>Write rate of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.iow",
            "description": "<p>Is this backend waiting for IO operations.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.relation",
            "description": "<p>OID of the relation targeted by the lock.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.type",
            "description": "<p>Type of lockable object.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.mode",
            "description": "<p>Name of the lock mode held or desired by this process.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.state",
            "description": "<p>State of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.duration",
            "description": "<p>Query duration (s).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.query",
            "description": "<p>Query.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"rows\":\n    [\n        {\n            \"pid\": 13309,\n            \"database\": \"test\",\n            \"user\": \"postgres\",\n            \"cpu\": 0.0,\n            \"memory\": 0.2,\n            \"read_s\": \"0.00B\",\n            \"write_s\": \"0.00B\",\n            \"iow\": \"N\",\n            \"relation\": \" \",\n            \"type\": \"transactionid\",\n            \"mode\": \"ExclusiveLock\",\n            \"state\": \"idle in transaction\",\n            \"duration\": 4126.98,\n            \"query\": \"UPDATE t1 SET id = 100000000 where id =1;\"\n        },\n        ...\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/activity/blocking",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/activity/__init__.py",
    "groupTitle": "Activity"
  },
  {
    "type": "post",
    "url": "/activity/kill",
    "title": "Terminate N backends.",
    "version": "0.0.1",
    "name": "ActivityKill",
    "group": "Activity",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String[]",
            "optional": false,
            "field": "pids",
            "description": "<p>List of process ID to terminate.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.backends",
            "description": "<p>List of backend status.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.backends.pid",
            "description": "<p>Process ID of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Boolean",
            "optional": false,
            "field": "response.backends.killes",
            "description": "<p>Was the backend killed ?</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"backends\":\n    [\n        {\"pid\": 13309, \"killed\": true},\n        ...\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X POST -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n    -H \"Content-Type: application/json\" --data '{\"pids\": [ 13309 ]}' \\\n    \"https://localhost:2345/activity/kill\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/activity/__init__.py",
    "groupTitle": "Activity"
  },
  {
    "type": "get",
    "url": "/activity/waiting",
    "title": "Get the list of backend waiting for lock acquisition.",
    "version": "0.0.1",
    "name": "ActivityWaiting",
    "group": "Activity",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.rows",
            "description": "<p>List of backends.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.pid",
            "description": "<p>Process ID of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.database",
            "description": "<p>Name of the database this backend is connected to.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.user",
            "description": "<p>Name of the user logged into this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.cpu",
            "description": "<p>CPU usage (%) of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.memory",
            "description": "<p>Memory usage (%) of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.read_s",
            "description": "<p>Read rate of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.write_s",
            "description": "<p>Write rate of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.iow",
            "description": "<p>Is this backend waiting for IO operations.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.relation",
            "description": "<p>OID of the relation targeted by the lock.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.type",
            "description": "<p>Type of lockable object.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.mode",
            "description": "<p>Name of the lock mode held or desired by this process.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.duration",
            "description": "<p>Query duration (s).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.state",
            "description": "<p>State of this backend.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.query",
            "description": "<p>Query.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"rows\":\n    [\n        {\n            \"pid\": 13532,\n            \"database\": \"test\",\n            \"user\": \"postgres\",\n            \"cpu\": 0.0,\n            \"memory\": 0.16,\n            \"read_s\": \"0.00B\",\n            \"write_s\": \"0.00B\",\n            \"iow\": \"N\",\n            \"relation\": \" \",\n            \"type\": \"transactionid\",\n            \"mode\": \"ShareLock\",\n            \"state\": \"active\",\n            \"duration\": 4.35,\n            \"query\": \"DELETE FROM t1 WHERE id = 1;\"\n        },\n        ...\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/activity/waiting",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/activity/__init__.py",
    "groupTitle": "Activity"
  },
  {
    "type": "get",
    "url": "/dashboard",
    "title": "Fetch all",
    "version": "0.0.1",
    "name": "GetDasboard",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "active_backends",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "active_backends.nb",
            "description": "<p>Number of PostgreSQL active backends.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "active_backends.time",
            "description": "<p>Timestamp (floating with ms) when the number of backend has been calculated.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "loadaverage",
            "description": "<p>System loadaverage.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "os_version",
            "description": "<p>Operating system version.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "hitratio",
            "description": "<p>PostgreSQL cache/hit ratio (%)</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "n_cpu",
            "description": "<p>Number of CPU.</p>"
          },
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "databases",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "databases.total_size",
            "description": "<p>PostgreSQL instance total size (with unit).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "databases.time",
            "description": "<p>Time when DBs informations have been retreived (HH:MM).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.databases",
            "description": "<p>Number of databases.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.total_commit",
            "description": "<p>Number of commited xact.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.total_rollback",
            "description": "<p>Number of rollbacked xact.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.timestamp",
            "description": "<p>Timestamp (floating with ms).</p>"
          },
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "memory",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.total",
            "description": "<p>Total amount of memory (kB).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.active",
            "description": "<p>Active memory (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.cached",
            "description": "<p>Memory used as OS cache (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.free",
            "description": "<p>Unused memory (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "hostname",
            "description": "<p>Machine hostname.</p>"
          },
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "cpu",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.iowait",
            "description": "<p>CPU cycles waiting for I/O operation (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.idle",
            "description": "<p>CPU IDLE time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.steal",
            "description": "<p>CPU steal time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.user",
            "description": "<p>CPU user time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.system",
            "description": "<p>CPU system time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "buffers",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "buffers.nb",
            "description": "<p>Allocated buffers from PostgreSQL bgwriter.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "buffers.time",
            "description": "<p>Timestamp (floating with ms) when the buffers number has been fetched.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"active_backends\":\n    {\n        \"nb\": 1,\n        \"time\": 1429617751.29224\n    },\n    \"loadaverage\": 0.28,\n    \"os_version\": \"Linux 3.16.0-34-generic x86_64\",\n    \"pg_version\": \"9.4.1\",\n    \"n_cpu\": \"4\",\n    \"hitratio\": 98.0,\n    \"databases\":\n    {\n        \"total_size\": \"1242 MB\",\n        \"time\": \"14:02\",\n        \"databases\": 4,\n        \"total_commit\": 16728291,\n        \"total_rollback\": 873\n    },\n    \"memory\": {\n        \"total\": 3950660,\n        \"active\": 46.9,\n        \"cached\": 20.2,\n        \"free\": 32.9\n    },\n    \"hostname\": \"neptune\",\n    \"cpu\":\n    {\n        \"iowait\": 0.0,\n        \"idle\": 97.5,\n        \"steal\": 0.0,\n        \"user\": 2.5,\n        \"system\": 0.0\n    },\n    \"buffers\":\n    {\n        \"nb\": 348247,\n        \"time\": 1429617751.276508\n    }\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" http://localhost:12345/dashboard",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/active_backends",
    "title": "PostgreSQL active backends",
    "version": "0.0.1",
    "name": "GetDasboardActiveBackends",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "active_backends",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "active_backends.nb",
            "description": "<p>Number of PostgreSQL active backends.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "active_backends.time",
            "description": "<p>Timestamp (floating with ms) when the number of backend has been calculated.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:38:02 GMT\nContent-type: application/json\n\n{\"active_backends\": {\"nb\": 1, \"time\": 1429702682.228157}}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/active_backends",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/buffers",
    "title": "PostgreSQL bgwriter buffers",
    "version": "0.0.1",
    "name": "GetDasboardBuffers",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "buffers",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "buffers.nb",
            "description": "<p>Allocated buffers from PostgreSQL bgwriter.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "buffers.time",
            "description": "<p>Timestamp (floating with ms) when the buffers number has been fetched.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:22:50 GMT\nContent-type: application/json\n\n{\"buffers\": {\"nb\": 348247, \"time\": 1429701770.303621}}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/buffers",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/cpu",
    "title": "CPU usage",
    "version": "0.0.1",
    "name": "GetDasboardCPU",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "cpu",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.iowait",
            "description": "<p>CPU cycles waiting for I/O operation (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.idle",
            "description": "<p>CPU IDLE time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.steal",
            "description": "<p>CPU steal time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.user",
            "description": "<p>CPU user time (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu.system",
            "description": "<p>CPU system time (%).</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:39:58 GMT\nContent-type: application/json\n\n{\"cpu\": {\"iowait\": 0.0, \"idle\": 97.5, \"steal\": 0.0, \"user\": 2.5, \"system\": 0.0}}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/cpu",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/databases",
    "title": "PostgreSQL instance size & number of DB",
    "version": "0.0.1",
    "name": "GetDasboardDatabases",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "databases",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "databases.total_size",
            "description": "<p>PostgreSQL instance total size (with unit).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "databases.time",
            "description": "<p>Time when DBs informations have been retreived (HH:MM).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.databases",
            "description": "<p>Number of databases.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.total_commit",
            "description": "<p>Number of commited xact.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "databases.total_rollback",
            "description": "<p>Number of rollbacked xact.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:52:05 GMT\nContent-type: application/json\n\n{\"databases\": {\"total_size\": \"1242 MB\", \"time\": \"13:52\", \"databases\": 4, \"total_commit\": 16728291, \"total_rollback\": 873}}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/databases",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/hitratio",
    "title": "PostgreSQL cache hit ratio",
    "version": "0.0.1",
    "name": "GetDasboardHitratio",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "hitratio",
            "description": "<p>PostgreSQL global cache/hit ratio (%)</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:27:27 GMT\nContent-type: application/json\n\n{\"hitratio\": 98.0}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/hitratio",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/hostname",
    "title": "Machine hostname",
    "version": "0.0.1",
    "name": "GetDasboardHostname",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "hostname",
            "description": "<p>Machine hostname.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:47:34 GMT\nContent-type: application/json\n\n{\"hostname\": \"neptune\"}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/hostname",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/loadaverage",
    "title": "System loadaverage",
    "version": "0.0.1",
    "name": "GetDasboardLoadaverage",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "loadaverage",
            "description": "<p>System loadaverage.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:41:31 GMT\nContent-type: application/json\n\n{\"loadaverage\": 0.31}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/loadaverage",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/memory",
    "title": "Memory usage",
    "version": "0.0.1",
    "name": "GetDasboardMemory",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "memory",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.total",
            "description": "<p>Total amount of memory (kB).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.active",
            "description": "<p>Active memory (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.cached",
            "description": "<p>Memory used as OS cache (%).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory.free",
            "description": "<p>Unused memory (%).</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:44:14 GMT\nContent-type: application/json\n\n{\"memory\": {\"total\": 3950660,\"active\": 56.6, \"cached\": 33.8, \"free\": 9.6}}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/memory",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/n_cpu",
    "title": "Number of CPU",
    "version": "0.0.1",
    "name": "GetDasboardNCpu",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "n_cpu",
            "description": "<p>Number of CPU.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:49:19 GMT\nContent-type: application/json\n\n{\"n_cpu\": 4}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/n_cpu",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/os_version",
    "title": "Operating system version",
    "version": "0.0.1",
    "name": "GetDasboardOSVersion",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "os_version",
            "description": "<p>Operating system version.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:49:19 GMT\nContent-type: application/json\n\n{\"os_version\": \"Linux 3.16.0-34-generic x86_64\"}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/os_version",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "get",
    "url": "/dashboard/pg_version",
    "title": "PostgreSQL version",
    "version": "0.0.1",
    "name": "GetDasboardPGVersion",
    "group": "Dashboard",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "pg_version",
            "description": "<p>PostgreSQL version.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 11:49:19 GMT\nContent-type: application/json\n\n{\"pg_version\": \"9.4.1\"}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -H \"X-Session: <session-id>\" http://localhost:12345/dashboard/pg_version",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/dashboard/__init__.py",
    "groupTitle": "Dashboard"
  },
  {
    "type": "delete",
    "url": "/pgconf/hba?version=:version",
    "title": "Remove a previous pg_hba.conf version.",
    "version": "0.0.1",
    "name": "DeletePgconfHBA",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "version",
            "description": "<p>Version number.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.version",
            "description": "<p>pg_hba.conf version.</p>"
          },
          {
            "group": "Success 200",
            "type": "Boolean",
            "optional": false,
            "field": "response.deleted",
            "description": "<p>Is deleted ?</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Fri, 12 Feb 2016 09:54:17 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"deleted\": true,\n    \"version\": \"2016-01-29T08:44:26\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X DELETE -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/hba?version=2016-01-29T08:44:26\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ],
        "404 error": [
          {
            "group": "404 error",
            "optional": false,
            "field": "error",
            "description": "<p>File version not found.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        },
        {
          "title": "404 error example",
          "content": "HTTP/1.0 404 Not Found\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Fri, 12 Feb 2016 10:00:55 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n\n{\"error\": \"Version 2016-01-29T08:44:26 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/configuration",
    "title": "Fetch all PostgreSQL settings.",
    "version": "0.0.1",
    "name": "GetPgconfConfiguration",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response",
            "description": "<p>List of settings category.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.category",
            "description": "<p>Category name.</p>"
          },
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.rows",
            "description": "<p>List of settings.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.context",
            "description": "<p>Context required to set the parameter's value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.rows.enum_vals",
            "description": "<p>Allowed values of an enum parameter (null for non-enum values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.min_val",
            "description": "<p>Minimum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.max_val",
            "description": "<p>Maximum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.vartype",
            "description": "<p>Parameter type (bool, enum, integer, real, or string).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.auto_val",
            "description": "<p>Parameter value set in auto configuration file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.auto_val_raw",
            "description": "<p>Parameter value set in auto configuration file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.file_val",
            "description": "<p>Parameter value set in main postgresql.conf file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.file_val_raw",
            "description": "<p>Parameter value set in main postgresql.conf file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.boot_val",
            "description": "<p>Parameter value assumed at server startup if the parameter is not otherwise set.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.unit",
            "description": "<p>Implicit unit of the parameter.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.desc",
            "description": "<p>Parameter description.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.name",
            "description": "<p>Parameter name.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.setting",
            "description": "<p>Parameter value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.setting_raw",
            "description": "<p>Parameter value (raw).</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n[\n    {\n        \"category\": \"Autovacuum\",\n        \"rows\":\n        [\n            {\n                \"context\": \"sighup\",\n                \"enumvals\": null,\n                \"max_val\": null,\n                \"vartype\": \"bool\",\n                \"auto_val\": \"off\",\n                \"auto_val_raw\": \"off\",\n                \"boot_val\": \"on\",\n                \"unit\": null,\n                \"desc\": \"Starts the autovacuum subprocess.\",\n                \"name\": \"autovacuum\",\n                \"min_val\": null,\n                \"setting\": \"off\",\n                \"setting_raw\": \"off\",\n                \"file_val\": null,\n                \"file_val_raw\": null\n            },\n            ...\n        ]\n    },\n    ...\n]",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/configuration",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/configuration/categories",
    "title": "Fetch settings categories names.",
    "version": "0.0.1",
    "name": "GetPgconfConfigurationCategories",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "categories",
            "description": "<p>List of settings category name.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"categories\":\n    [\n        \"Autovacuum\",\n        \"Client Connection Defaults / Locale and Formatting\",\n        \"Client Connection Defaults / Other Defaults\",\n        ...\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/configuration/categories",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/configuration/category/:categoryname",
    "title": "Fetch settings for one category, based on categoryname.",
    "version": "0.0.1",
    "name": "GetPgconfConfigurationCategory",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "categoryname",
            "description": "<p>Category Name.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response",
            "description": "<p>List of settings category.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.category",
            "description": "<p>Category name.</p>"
          },
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.rows",
            "description": "<p>List of settings.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.context",
            "description": "<p>Context required to set the parameter's value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.rows.enum_vals",
            "description": "<p>Allowed values of an enum parameter (null for non-enum values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.min_val",
            "description": "<p>Minimum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.rows.max_val",
            "description": "<p>Maximum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.vartype",
            "description": "<p>Parameter type (bool, enum, integer, real, or string).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.auto_val",
            "description": "<p>Parameter value set in auto configuration file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.auto_val_raw",
            "description": "<p>Parameter value set in auto configuration file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.file_val",
            "description": "<p>Parameter value set in main postgresql.conf file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.file_val_raw",
            "description": "<p>Parameter value set in main postgresql.conf file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.boot_val",
            "description": "<p>Parameter value assumed at server startup if the parameter is not otherwise set.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.unit",
            "description": "<p>Implicit unit of the parameter.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.desc",
            "description": "<p>Parameter description.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.name",
            "description": "<p>Parameter name.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.setting",
            "description": "<p>Parameter value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.rows.setting_raw",
            "description": "<p>Parameter value (raw).</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Wed, 10 Feb 2016 09:56:30 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n[\n    {\n        \"category\": \"Autovacuum\",\n        \"rows\":\n        [\n            {\n                \"context\": \"sighup\",\n                \"enumvals\": null,\n                \"max_val\": null,\n                \"vartype\": \"bool\",\n                \"auto_val\": \"on\",\n                \"auto_val_raw\": \"on\",\n                \"boot_val\": \"on\",\n                \"unit\": null,\n                \"desc\": \"Starts the autovacuum subprocess. \",\n                \"name\": \"autovacuum\",\n                \"min_val\": null,\n                \"setting\": \"on\",\n                \"setting_raw\": \"on\",\n                \"file_val\": null,\n                \"file_val_raw\": null\n            },\n            ...\n        ]\n    }\n]",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/configuration/category/Autovacuum\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/configuration/status",
    "title": "Shows settings waiting for PostgreSQL reload and/or restart",
    "version": "0.0.1",
    "name": "GetPgconfConfigurationStatus",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Boolean",
            "optional": false,
            "field": "response.restart_pending",
            "description": "<p>Does PostgreSQL need to be restarted ?</p>"
          },
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.restart_changes",
            "description": "<p>List of settings.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.context",
            "description": "<p>Context required to set the parameter's value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.restart_changes.enum_vals",
            "description": "<p>Allowed values of an enum parameter (null for non-enum values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.restart_changes.min_val",
            "description": "<p>Minimum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.restart_changes.max_val",
            "description": "<p>Maximum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.vartype",
            "description": "<p>Parameter type (bool, enum, integer, real, or string).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.auto_val",
            "description": "<p>Parameter value set in auto configuration file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.auto_val_raw",
            "description": "<p>Parameter value set in auto configuration file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.file_val",
            "description": "<p>Parameter value set in main postgresql.conf file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.file_val_raw",
            "description": "<p>Parameter value set in main postgresql.conf file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.boot_val",
            "description": "<p>Parameter value assumed at server startup if the parameter is not otherwise set.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.unit",
            "description": "<p>Implicit unit of the parameter.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.desc",
            "description": "<p>Parameter description.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.name",
            "description": "<p>Parameter name.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.setting",
            "description": "<p>Parameter value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.setting_raw",
            "description": "<p>Parameter value (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.restart_changes.pending_val",
            "description": "<p>Pending value.</p>"
          },
          {
            "group": "Success 200",
            "type": "Boolean",
            "optional": false,
            "field": "response.reload_pending",
            "description": "<p>Does PostgreSQL need to be reloaded ?</p>"
          },
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.reload_changes",
            "description": "<p>List of settings.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.context",
            "description": "<p>Context required to set the parameter's value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.reload_changes.enum_vals",
            "description": "<p>Allowed values of an enum parameter (null for non-enum values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.reload_changes.min_val",
            "description": "<p>Minimum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "response.reload_changes.max_val",
            "description": "<p>Maximum allowed value of the parameter (null for non-numeric values).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.vartype",
            "description": "<p>Parameter type (bool, enum, integer, real, or string).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.auto_val",
            "description": "<p>Parameter value set in auto configuration file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.auto_val_raw",
            "description": "<p>Parameter value set in auto configuration file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.file_val",
            "description": "<p>Parameter value set in main postgresql.conf file.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.file_val_raw",
            "description": "<p>Parameter value set in main postgresql.conf file (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.boot_val",
            "description": "<p>Parameter value assumed at server startup if the parameter is not otherwise set.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.unit",
            "description": "<p>Implicit unit of the parameter.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.desc",
            "description": "<p>Parameter description.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.name",
            "description": "<p>Parameter name.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.setting",
            "description": "<p>Parameter value.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.setting_raw",
            "description": "<p>Parameter value (raw).</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.reload_changes.pending_val",
            "description": "<p>Pending value.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Wed, 10 Feb 2016 09:56:30 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"restart_changes\":\n    [\n        {\n            \"context\": \"postmaster\",\n            \"setting_raw\": \"128MB\",\n            \"enumvals\": null,\n            \"max_val\": 1073741823,\n            \"vartype\": \"integer\",\n            \"auto_val\": 32768,\n            \"file_val_raw\": \"128MB\",\n            \"boot_val\": 1024,\n            \"unit\": \"8kB\",\n            \"desc\": \"Sets the number of shared memory buffers used by the server. \",\n            \"name\": \"shared_buffers\",\n            \"auto_val_raw\": \"256MB\",\n            \"min_val\": 16,\n            \"setting\": 16384,\n            \"file_val\": 16384,\n            \"pending_val\": \"256MB\"\n        }\n    ],\n    \"restart_pending\": true,\n    \"reload_pending\": false,\n    \"reload_changes\":\n    [\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/configuration/status\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/hba?version=:version",
    "title": "Get pg_hba.conf records",
    "version": "0.0.1",
    "name": "GetPgconfHBA",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "version",
            "description": "<p>Version number, if omitted, current file is considered.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "response.entries",
            "description": "<p>HBA records list.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.entries.connection",
            "description": "<p>The record matches connection attempts using Unix-domain sockets (local) or using TCP/IP (host) or using TCP/IP, but only when the connection is made with SSL encryption (hostssl) or using TCP/IP that do not use SSL.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.entries.database",
            "description": "<p>Specifies which database name(s) this record matches.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.entries.user",
            "description": "<p>Specifies which user name(s) this record matches.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.entries.address",
            "description": "<p>Specifies the client machine address(es) that this record matches. Hostname or IP address range.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.entries.auth_method",
            "description": "<p>Specifies the authentication method to use when a connection matches this record.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.entries.auth_options",
            "description": "<p>Specifies options for the authentication method.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.version",
            "description": "<p>pg_hba.conf file version, null if current.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.filepath",
            "description": "<p>pg_hba.conf file path.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Wed, 10 Feb 2016 09:56:30 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json*\n{\n    \"entries\":\n    [\n        {\n            \"database\": \"all\",\n            \"connection\": \"local\",\n            \"auth_options\": \"\",\n            \"user\": \"postgres\",\n            \"address\": \"\",\n            \"auth_method\": \"ident\"\n        },\n        ...\n    ],\n    \"version\": null,\n    \"filepath\": \"/etc/postgresql/9.4/main/pg_hba.conf\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/hba\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ],
        "404 error": [
          {
            "group": "404 error",
            "optional": false,
            "field": "error",
            "description": "<p>File version not found.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        },
        {
          "title": "404 error example",
          "content": "HTTP/1.0 404 Not Found\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Thu, 11 Feb 2016 09:04:02 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n\n{\"error\": \"Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/hba/options",
    "title": "Get HBA potential values for each column.",
    "version": "0.0.1",
    "name": "GetPgconfHBAOptions",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.connection",
            "description": "<p>Connection field potential values.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.database",
            "description": "<p>Database field potential values.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.user",
            "description": "<p>User field potential values.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.auth_method",
            "description": "<p>Authentication methods.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Fri, 12 Feb 2016 10:48:57 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"connection\": [ \"local\", \"host\", \"hostssl\", \"hostnossl\" ],\n    \"database\": [ \"all\", \"sameuser\", \"samerole\", \"db1\" ],\n    \"user\": [ \"all\", \"user1\", \"+group1\" ],\n    \"auth_method\": [ \"trust\", \"reject\", ... ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/hba/options\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/hba/raw?version=:version",
    "title": "Get pg_hba.conf raw content",
    "version": "0.0.1",
    "name": "GetPgconfHBARaw",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "version",
            "description": "<p>Version number, if omitted, current file is considered.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response.content",
            "description": "<p>pg_hba.conf file raw content.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.version",
            "description": "<p>pg_hba.conf file version, null if current.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.filepath",
            "description": "<p>pg_hba.conf file path.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Thu, 11 Feb 2016 13:40:51 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"content\": \"# PostgreSQL Client Authentication Configuration File\\r\\n# ===================================================\\r\\n# Database administrative login by Unix domain socket\\r\\nlocal   all             postgres                           ident #tutu\\r\\nlocal   all             all                                md5 #toto\\r\\n# TYPE  DATABASE        USER            ADDRESS                 METHOD\\r\\n# \\\"local\\\" is for Unix domain socket connections only\\r\\nlocal   all             all                                     md5\\r\\n# IPv4 local connections:\\r\\nhost    all             all             127.0.0.1/32            md5\\r\\n# IPv6 local connections:\\r\\nhost    all             all             ::1/128                 md5\\r\\n# Allow replication connections from localhost, by a user with the\\r\\n# replication privilege.\\r\\nlocal   replication     postgres                                peer\\r\\nhost    replication     postgres        127.0.0.1/32            md5\\r\\nhost    replication     postgres        ::1/128                 md5\\r\\nhost\\treplication\\t\\treplicator\\t\\t192.168.1.40/32\\t\\t\\ttrust #test\\r\\n# test ok\\r\\nhost    all     all     192.168.1.0/24  trust\\r\\nhost    all     all     192.168.1.0/24  trust\\r\\n\",\n    \"version\": \"2016-01-29T08:46:07\",\n    \"filepath\": \"/etc/postgresql/9.4/main/pg_hba.conf\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/hba/raw?version=2016-01-29T08:46:09\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ],
        "404 error": [
          {
            "group": "404 error",
            "optional": false,
            "field": "error",
            "description": "<p>File version not found.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        },
        {
          "title": "404 error example",
          "content": "HTTP/1.0 404 Not Found\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Thu, 11 Feb 2016 09:04:02 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n\n{\"error\": \"Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/hba/versions",
    "title": "Get the list of pg_hba.conf versions.",
    "version": "0.0.1",
    "name": "GetPgconfHBAVersions",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "response.versions",
            "description": "<p>List of versions, desc. sorting.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.filepath",
            "description": "<p>pg_hba.conf file path.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Fri, 12 Feb 2016 10:38:10 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"versions\":\n    [\n        \"2016-02-11T18:01:35\",\n        \"2016-02-11T16:43:51\",\n        \"2016-02-11T16:43:36\",\n        ...\n    ],\n    \"filepath\": \"/etc/postgresql/9.4/main/pg_hba.conf\"}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/hba/versions\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/pgconf/pg_ident",
    "title": "Get pg_ident.conf raw content",
    "version": "0.0.1",
    "name": "GetPgconfPGIdentRaw",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response.content",
            "description": "<p>pg_ident.conf file raw content.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.filepath",
            "description": "<p>pg_ident.conf file path.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Fri, 12 Feb 2016 10:48:57 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"content\": \"# PostgreSQL User Name Maps\\r\\n# =========================\\r\\n ... \",\n    \"filepath\": \"/etc/postgresql/9.4/main/pg_ident.conf\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            https://localhost:2345/pgconf/pg_ident\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "post",
    "url": "/pgconf/configuration",
    "title": "Update setting/s value.",
    "version": "0.0.1",
    "name": "PostPgconfConfiguration",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "Object[]",
            "optional": false,
            "field": "settings",
            "description": "<p>List of settings.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "settings.name",
            "description": "<p>Setting name.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "settings.setting",
            "description": "<p>Setting value.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "settings",
            "description": "<p>List of settings updated.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "settings.setting",
            "description": "<p>Setting value.</p>"
          },
          {
            "group": "Success 200",
            "type": "Boolean",
            "optional": false,
            "field": "settings.restart",
            "description": "<p>Does PostgreSQL need to be restarted.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "settings.name",
            "description": "<p>Setting name.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "settings.previous_setting",
            "description": "<p>Previous setting value.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:57:52 GMT\nContent-type: application/json\n{\n    \"settings\":\n    [\n        {\n            \"setting\": \"on\",\n            \"restart\": false,\n            \"name\": \"autovacuum\",\n            \"previous_setting\": \"off\"\n        }\n    ]\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X POST -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n            -H \"Content-Type: application/json\" \\\n            --data '{\"settings\": [{\"name\": \"autovacuum\", \"setting\": \"on\"}]}' \\\n            https://localhost:2345/pgconf/configuration",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ],
        "400 error": [
          {
            "group": "400 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid json format.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        },
        {
          "title": "400 error example",
          "content": "HTTP/1.0 400 Bad request\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid json format: Expecting ',' delimiter: line 1 column 51 (char 50).\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "post",
    "url": "/pgconf/hba",
    "title": "Replace pg_hba.conf file content.",
    "version": "0.0.1",
    "name": "PostPgconfHBA",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "Object[]",
            "optional": false,
            "field": "entries",
            "description": "<p>List of records.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "entries.connection",
            "description": "<p>The record matches connection attempts using Unix-domain sockets (local) or using TCP/IP (host) or using TCP/IP, but only when the connection is made with SSL encryption (hostssl) or using TCP/IP that do not use SSL.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "entries.database",
            "description": "<p>Specifies which database name(s) this record matches.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "entries.user",
            "description": "<p>Specifies which user name(s) this record matches.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "entries.address",
            "description": "<p>Specifies the client machine address(es) that this record matches. Hostname or IP address range.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "entries.auth_method",
            "description": "<p>Specifies the authentication method to use when a connection matches this record.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "entries.auth_options",
            "description": "<p>Specifies options for the authentication method.</p>"
          },
          {
            "group": "Parameter",
            "type": "Boolean",
            "optional": false,
            "field": "new_version",
            "description": "<p>Create a new version of current pg_hba.conf before writing new content.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.last_version",
            "description": "<p>pg_hba.conf last file version.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.filepath",
            "description": "<p>pg_hba.conf file path.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Thu, 11 Feb 2016 14:26:19 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"last_version\": \"2016-02-11T15:26:19\",\n    \"filepath\": \"/etc/postgresql/9.4/main/pg_hba.conf\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X POST -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n                -H \"Content-Type: application/json\" \\\n                --data '{\"entries\": [{\"connection\": \"local\", \"user\": \"all\", \"database\": \"all\", \"auth_method\": \"peer\"}, ... ], \"new_version\": true}' \\\n            https://localhost:2345/pgconf/hba\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "post",
    "url": "/pgconf/hba/raw",
    "title": "Replace pg_hba.conf file content (raw mode).",
    "version": "0.0.1",
    "name": "PostPgconfHBARaw",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "content",
            "description": "<p>pg_hba.conf content (raw).</p>"
          },
          {
            "group": "Parameter",
            "type": "Boolean",
            "optional": false,
            "field": "new_version",
            "description": "<p>Create a new version of current pg_hba.conf before writing new content.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.last_version",
            "description": "<p>pg_hba.conf last file version.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "response.filepath",
            "description": "<p>pg_hba.conf file path.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Thu, 11 Feb 2016 14:26:19 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"last_version\": \"2016-02-11T15:26:19\",\n    \"filepath\": \"/etc/postgresql/9.4/main/pg_hba.conf\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X POST -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n                -H \"Content-Type: application/json\" \\\n                --data '{\"content\": \"local all all md5\\r\\n ...\", \"new_version\": true}' \\\n            https://localhost:2345/pgconf/hba/raw\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "post",
    "url": "/pgconf/pg_ident",
    "title": "Replace pg_ident.conf file content (raw mode).",
    "version": "0.0.1",
    "name": "PostPgconfPGIdentRaw",
    "group": "Pgconf",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "content",
            "description": "<p>pg_ident.conf content (raw).</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object",
            "optional": false,
            "field": "response",
            "description": ""
          },
          {
            "group": "Success 200",
            "type": "Boolean",
            "optional": false,
            "field": "response.update",
            "description": "<p>Has pg_ident.conf been updated ?</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.9\nDate: Thu, 11 Feb 2016 14:26:19 GMT\nAccess-Control-Allow-Origin: *\nContent-type: application/json\n{\n    \"update\": true\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X POST -H \"X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e\" \\\n                -H \"Content-Type: application/json\" \\\n                --data '{\"content\": \"# PostgreSQL User Name Maps\\r\\n ...\"}' \\\n            https://localhost:2345/pgconf/pg_ident\"",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Parameter 'X-Session' is malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 09:58:00 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/plugins/pgconf/__init__.py",
    "groupTitle": "Pgconf"
  },
  {
    "type": "get",
    "url": "/discover",
    "title": "Get global informations about the env.",
    "version": "0.0.1",
    "name": "Discover",
    "group": "User",
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "hostname",
            "description": "<p>Hostname.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "pg_data",
            "description": "<p>PostgreSQL data directory.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "pg_port",
            "description": "<p>PostgreSQL listen port.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "pg_version",
            "description": "<p>PostgreSQL version.</p>"
          },
          {
            "group": "Success 200",
            "type": "String[]",
            "optional": false,
            "field": "plugins",
            "description": "<p>List or available plugins.</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "memory_size",
            "description": "<p>Memory size (bytes).</p>"
          },
          {
            "group": "Success 200",
            "type": "Number",
            "optional": false,
            "field": "cpu",
            "description": "<p>Number of CPU.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:33:19 GMT\nContent-type: application/json\n{\n    \"hostname\": \"neptune\",\n    \"pg_data\": \"/var/lib/postgresql/9.4/main\",\n    \"pg_port\": 5432,\n    \"plugins\": [\"monitoring\", \"dashboard\", \"settings\", \"administration\", \"activity\"],\n    \"memory_size\": 8241508352,\n    \"pg_version\": \"PostgreSQL 9.4.5 on x86_64-unknown-linux-gnu, compiled by gcc (Ubuntu 4.9.2-10ubuntu13) 4.9.2, 64-bit\",\n    \"cpu\": 4\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k https://localhost:2345/discover",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ]
      }
    },
    "filename": "./temboardagent/api.py",
    "groupTitle": "User"
  },
  {
    "type": "get",
    "url": "/notifications",
    "title": "Get all notifications.",
    "version": "0.0.1",
    "name": "Notifications",
    "group": "User",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Object[]",
            "optional": false,
            "field": "notifications",
            "description": "<p>List of notifications.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "notifications.date",
            "description": "<p>Notification datetime.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "notifications.username",
            "description": "<p>Username.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "notifications.message",
            "description": "<p>Message.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:33:19 GMT\nContent-type: application/json\n\n[\n    {\"date\": \"2016-04-11T16:12:38\", \"username\": \"julien\", \"message\": \"Login\"},\n    {\"date\": \"2016-04-11T16:02:03\", \"username\": \"julien\", \"message\": \"Login\"},\n    {\"date\": \"2016-04-11T15:51:15\", \"username\": \"julien\", \"message\": \"HBA file version '2016-04-11T15:32:53' removed.\"},\n    {\"date\": \"2016-04-11T15:51:10\", \"username\": \"julien\", \"message\": \"HBA file version '2016-04-11T15:47:26' removed.\"},\n    {\"date\": \"2016-04-11T15:51:04\", \"username\": \"julien\", \"message\": \"HBA file version '2016-04-11T15:48:50' removed.\"},\n    {\"date\": \"2016-04-11T15:50:57\", \"username\": \"julien\", \"message\": \"PostgreSQL reload\"},\n    {\"date\": \"2016-04-11T15:50:57\", \"username\": \"julien\", \"message\": \"HBA file updated\"},\n    {\"date\": \"2016-04-11T15:48:50\", \"username\": \"julien\", \"message\": \"PostgreSQL reload\"}\n]",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63\" https://localhost:2345/notifications",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session ID.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Session ID malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:36:33 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:37:23 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/api.py",
    "groupTitle": "User"
  },
  {
    "type": "get",
    "url": "/profile",
    "title": "Get current user name.",
    "version": "0.0.1",
    "name": "Profile",
    "group": "User",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "username",
            "description": "<p>Username.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:33:19 GMT\nContent-type: application/json\n{\n    \"username\": \"julien\"\n}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63\" https://localhost:2345/profile",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session ID.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Session ID malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:36:33 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:37:23 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/api.py",
    "groupTitle": "User"
  },
  {
    "type": "get",
    "url": "/login",
    "title": "User login",
    "version": "0.0.1",
    "name": "UserLogin",
    "group": "User",
    "parameter": {
      "fields": {
        "Parameter": [
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "username",
            "description": "<p>Username.</p>"
          },
          {
            "group": "Parameter",
            "type": "String",
            "optional": false,
            "field": "password",
            "description": "<p>Password.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "sessions",
            "description": "<p>Session ID.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:19:48 GMT\nContent-type: application/json\n\n{\"session\": \"fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63\"}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -X POST -H \"Content-Type: application/json\" -d '{\"username\": \"julien\", \"password\": \"password12!\"}' \\\n    https://localhost:2345/login",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "404 error": [
          {
            "group": "404 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid username or password.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Username or password malformed or missing.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "404 error example",
          "content": "HTTP/1.0 404 Not Found\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:20:33 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid username/password.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:21:01 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'password' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/api.py",
    "groupTitle": "User"
  },
  {
    "type": "get",
    "url": "/logout",
    "title": "User logout",
    "version": "0.0.1",
    "name": "UserLogout",
    "group": "User",
    "header": {
      "fields": {
        "Header": [
          {
            "group": "Header",
            "type": "String",
            "optional": false,
            "field": "X-Session",
            "description": "<p>Session ID.</p>"
          }
        ]
      }
    },
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "type": "Bool",
            "optional": false,
            "field": "logout",
            "description": "<p>True if logout succeeds.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "Success-Reponse:",
          "content": "HTTP/1.0 200 OK\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:33:19 GMT\nContent-type: application/json\n\n{\"logout\": true}",
          "type": "json"
        }
      ]
    },
    "examples": [
      {
        "title": "Example usage:",
        "content": "curl -k -H \"X-Session: fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63\" https://localhost:2345/logout",
        "type": "curl"
      }
    ],
    "error": {
      "fields": {
        "500 error": [
          {
            "group": "500 error",
            "optional": false,
            "field": "error",
            "description": "<p>Internal error.</p>"
          }
        ],
        "401 error": [
          {
            "group": "401 error",
            "optional": false,
            "field": "error",
            "description": "<p>Invalid session ID.</p>"
          }
        ],
        "406 error": [
          {
            "group": "406 error",
            "optional": false,
            "field": "error",
            "description": "<p>Session ID malformed.</p>"
          }
        ]
      },
      "examples": [
        {
          "title": "401 error example",
          "content": "HTTP/1.0 401 Unauthorized\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:36:33 GMT\nContent-type: application/json\n\n{\"error\": \"Invalid session.\"}",
          "type": "json"
        },
        {
          "title": "406 error example",
          "content": "HTTP/1.0 406 Not Acceptable\nServer: temboard-agent/0.0.1 Python/2.7.8\nDate: Wed, 22 Apr 2015 12:37:23 GMT\nContent-type: application/json\n\n{\"error\": \"Parameter 'X-Session' is malformed.\"}",
          "type": "json"
        }
      ]
    },
    "filename": "./temboardagent/api.py",
    "groupTitle": "User"
  },
  {
    "success": {
      "fields": {
        "Success 200": [
          {
            "group": "Success 200",
            "optional": false,
            "field": "varname1",
            "description": "<p>No type.</p>"
          },
          {
            "group": "Success 200",
            "type": "String",
            "optional": false,
            "field": "varname2",
            "description": "<p>With type.</p>"
          }
        ]
      }
    },
    "type": "",
    "url": "",
    "version": "0.0.0",
    "filename": "./doc/html/main.js",
    "group": "_home_julien_Development_python_temboard_temboard_agent_doc_html_main_js",
    "groupTitle": "_home_julien_Development_python_temboard_temboard_agent_doc_html_main_js",
    "name": ""
  }
] });
