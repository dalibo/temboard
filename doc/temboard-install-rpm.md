# temBoard installation from RPM package on RHEL / CentOS 7

## Package repository setup

The following YUM repository are required to install `temboard`:

* [yum.postgresql.org](http://yum.postgresql.org/repopackages.php) for PostgreSQL
* [Dalibo Labs package repository](http://yum.dalibo.org/labs/) for temBoard

### RHEL / CentOS 7

Install the `dalibo-labs` package with GPG key and .repo from https://yum.dalibo.org/labs/dalibo-labs-1-1.noarch.rpm

```console
sudo yum install -y https://yum.dalibo.org/labs/dalibo-labs-1-1.noarch.rpm
sudo yum makecache fast
sudo yum repolist
```

You can also setup YUM manually with the following snippet in `/etc/yum.repos.d/dalibolabs.repo`:

```ini
[dalibolabs]
name=Dalibo Labs - CentOS/RHEL $releasever - $basearch
baseurl=https://yum.dalibo.org/labs/CentOS$releasever-$basearch
enabled=1
gpgcheck=0
```

Finally, the PostgreSQL packages from RHEL / CentOS 7 being too old, you need to add the YUM repository of the PostgreSQL Global Development Group, from [yum.postgresql.org](http://yum.postgresql.org/repopackages.php). Here is an example to install PostgreSQL 10, you should check the site and use the latest production version of PostgreSQL. PostgreSQL 9.5 or newer is required:

```
sudo rpm -ivh https://download.postgresql.org/pub/repos/yum/10/redhat/rhel-7-x86_64/pgdg-centos10-10-2.noarch.rpm
```

## Installation

With the YUM repositories set up, temBoard can be installed with yum:

```
sudo yum install temboard
```

The database access must be set up otherwise the temboard service will not start. See `doc/temboard-repository-setup.md`.

## Firewall and SELinux

`temboard` works well with the default enforced configuration of SELinux.

To access the temboard web UI, you may need to configure the firewall to allow access on TCP port `8888`, which is the default port. It can be configured in `/etc/temboard/temboard.conf`, see `doc/temboard-configuration.md`.

## Operations

### Important files and directories

- /etc/temboard: stores the `temboard.conf` configuration file and SSL certificates
- /var/log/temboard: stores the logs
- /var/run/temboard: stores the PID file

### Start


```
sudo systemctl start temboard
```

### Start at boot time

```
sudo systemctl enable temboard
```

### Status

```
sudo systemctl status temboard
```

### Reload configuration

```
sudo systemctl reload temboard
```

### Stop

```
sudo systemctl stop temboard
```
