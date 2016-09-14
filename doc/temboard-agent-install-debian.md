# temBoard agent installation from debian package (jessie)

## Package building

To create a new debian package from `temboard-agent` sources, the packages `dpkg-dev` and `debhelper` have to be installed.
```
$ sudo apt-get install dpkg-dev debhelper
```

Then, you need to go in `temboard/temboard-agent/debian` directory and execute the script `make_deb.sh`. Once the script executed, the .deb file can be found in `temboard/` directory.

## Installation

```
$ sudo dpkg -i temboard-agent_0.0.1-7_all.deb
```


## Operations

### Start the agent

```
$ sudo service temboard-agent start
```

### Status

```
$ sudo service temboard-agent status

● temboard-agent.service - LSB: Start temboard-agent
   Loaded: loaded (/etc/init.d/temboard-agent)
   Active: active (running) since Thu 2016-08-25 15:24:37 CEST; 1min 33s ago
  Process: 10342 ExecStart=/etc/init.d/temboard-agent start (code=exited, status=0/SUCCESS)
   CGroup: /system.slice/temboard-agent.service
           ├─10346 /usr/bin/python /usr/bin/temboard-agent -c /etc/temboard-agent/temboard-agent.conf -d -p /var/run/postgresql/temboard-agent.pid
           └─10348 /usr/bin/python /usr/bin/temboard-agent -c /etc/temboard-agent/temboard-agent.conf -d -p /var/run/postgresql/temboard-agent.pid

Aug 25 15:24:37 debian-tbd-agent temboard-agent[10342]: Starting: temboard-agent.
```

### Reload configuration

```
$ sudo service temboard-agent reload
```

### Stop the agent

```
$ sudo service temboard-agent stop
```
