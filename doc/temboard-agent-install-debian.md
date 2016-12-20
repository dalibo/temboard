# temBoard agent installation from debian package (jessie)

## Package repository setup

Add the temboard repository to the configuration of APT. Create /etc/apt/sources.list.d/temboard.list with the following contents :

```
deb https://packages.temboard.io/apt/ jessie main
```

Ensure APT can handle HTTPS:

```
sudo apt-get install apt-transport-https
```

Add the GPG key of the repository and update the packages list:

```
sudo apt-get install wget ca-certificates
wget -q -O - https://packages.temboard.io/apt/265B525B.asc | sudo apt-key add -
sudo apt-get update
```


## Installation

```
sudo apt-get install temboard-agent
```

## Configuration

Before starting the agent, see `doc/temboard-agent-configuration.md` for post-installation tasks.

## Operations

### Important files and directories

- /etc/temboard-agent: stores the `temboard-agent.conf` configuration file and SSL certificates
- /var/lib/temboard-agent: stores the data of the agent
- /var/log/temboard-agent: stores the logs
- /var/run/temboard-agent: stores the PID file


### Start the agent

```
sudo service temboard-agent start
```

### Status

```
sudo service temboard-agent status

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
sudo service temboard-agent reload
```

### Stop the agent

```
sudo service temboard-agent stop
```

## Package building

To create a new debian package from `temboard-agent` sources, the packages `dpkg-dev` and `debhelper` have to be installed.
```
sudo apt-get install dpkg-dev debhelper
```

Then, you need to go in `temboard/temboard-agent/debian` directory and execute the script `make_deb.sh`. Once the script executed, the .deb file can be found in `temboard/` directory.
