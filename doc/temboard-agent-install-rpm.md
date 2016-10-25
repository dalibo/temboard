# temBoard agent installation from rpm package on RHEL / CentOS 5 and later

## Package repository setup

### RHEL / CentOS 5

Install the `packages.temboard.io` repository by creating the `/etc/yum.repos.d/temboard.repo` file with the following contents:

```
[temboard]
name=temBoard Packages for Enterprise Linux 5
baseurl=https://packages.temboard.io/yum/rhel5/
enabled=1
gpgcheck=0
```

### RHEL / CentOS 6

Install the `packages.temboard.io` repository by creating the `/etc/yum.repos.d/temboard.repo` file with the following contents:

```
[temboard]
name=temBoard Packages for Enterprise Linux 6
baseurl=https://packages.temboard.io/yum/rhel6/
enabled=1
gpgcheck=0
```

### RHEL / CentOS 7

Install the `packages.temboard.io` repository by creating the `/etc/yum.repos.d/temboard.repo` file with the following contents:

```
[temboard]
name=temBoard Packages for Enterprise Linux 7
baseurl=https://packages.temboard.io/yum/rhel7/
enabled=1
gpgcheck=0
```


## Installation

With the YUM repositories set up, the temBoard agent can be installed with `yum`:

```
yum install temboard-agent
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

On RHEL / CentOS 5 and 6:
```
sudo service temboard-agent start
```

On RHEL / CentOS 7:
```
sudo systemctl start temboard-agent
```

### Start at boot time

On RHEL / CentOS 5 and 6:

```
chkconfig temboard-agent on
```

On RHEL / CentOS 7:

```
systemctl enable temboard-agent
```

### Status

On RHEL / CentOS 6:

```
ps auxf | grep temboard-agent
```

On RHEL / CentOS 7:

```
systemctl status temboard-agent
```

### Reload configuration

On RHEL / CentOS 6:

```
service temboard-agent reload
```

On RHEL / CentOS 7:

```
systemctl reload temboard-agent
```

### Stop

On RHEL / CentOS 6:

```
service temboard-agent stop
```

On RHEL / CentOS 7:

```
systemctl stop temboard-agent
```
