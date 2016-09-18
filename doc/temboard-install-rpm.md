# temBoard installation from rpm package on RHEL / CentOS 6 and later

## Package repository setup

The following YUM repository are required to install `temboard`:

* [Extra Packages for Enterprise Linux](https://fedoraproject.org/wiki/EPEL) for newer versions of some dependencies
* [yum.postgresql.org](http://yum.postgresql.org/repopackages.php) for PostgreSQL 9.5
* [temBoard package repository](https://packages.temboard.io/yum/) for temBoard

### RHEL / CentOS 6

Install the `packages.temboard.io` repository by creating the `/etc/yum.repos.d/temboard.repo` file with the following contents:

```
[temboard]
name=temBoard Packages for Enterprise Linux 6
baseurl=https://packages.temboard.io/yum/rhel6/
enabled=1
gpgcheck=0
```

The packages available from `packages.temboard.io` relies on the EPEL repository (see [Extra Packages for Enterprise Linux](https://fedoraproject.org/wiki/EPEL)). The easiest way to setup this repository is to use the `epel-release` package:

```
# rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
```

Finally, the PostgreSQL packages from RHEL / CentOS 6 being too old, you need to add the YUM repository of the PostgreSQL Global Development Group, from [yum.postgresql.org](http://yum.postgresql.org/repopackages.php). Here is an example to install PostgreSQL 9.5, you should check the site and use the latest production version of PostgreSQL. PostgreSQL 9.5 or newer is required:

```
# rpm -ivh https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-6-x86_64/pgdg-centos95-9.5-2.noarch.rpm
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

The packages available from `packages.temboard.io` relies on the EPEL repository (see [Extra Packages for Enterprise Linux](https://fedoraproject.org/wiki/EPEL)). The easiest way to setup this repository is to use the `epel-release` package:

```
# rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

Finally, the PostgreSQL packages from RHEL / CentOS 7 being too old, you need to add the YUM repository of the PostgreSQL Global Development Group, from [yum.postgresql.org](http://yum.postgresql.org/repopackages.php). Here is an example to install PostgreSQL 9.5, you should check the site and use the latest production version of PostgreSQL. PostgreSQL 9.5 or newer is required:

```
# rpm -ivh https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-7-x86_64/pgdg-centos95-9.5-2.noarch.rpm
```

## Installation

With the YUM repositories set up, temBoard can be installed with yum:

```
# yum install temboard
```

The database access must be set up otherwise the temboard service will not start. See `doc/temboard-repository-setup.md`.

## Firewall and SELinux

`temboard` works well with the default enforced configuration of SELinux.

To access the temboard web UI, you may need to configure the firewall to allow access on TCP port 8888, which is the default port. It can be configured in `/etc/temboard/temboard.conf`, see `doc/temboard-configuration.md`.

## Operations

### Important files and directories

- /etc/temboard: stores the `temboard.conf` configuration file and SSL certificates
- /var/log/temboard: stores the logs
- /var/run/temboard: stores the PID file

### Start

On RHEL / CentOS 6:

```
# service temboard start
```

On RHEL / CentOS 7:

```
# systemctl start temboard
```

### Start at boot time

On RHEL / CentOS 6:

```
# chkconfig temboard on
```

On RHEL / CentOS 7:

```
# systemctl enable temboard
```

### Status

On RHEL / CentOS 6:

```
# ps auxf | grep temboard
```

On RHEL / CentOS 7:

```
# systemctl status temboard
```

### Reload configuration

On RHEL / CentOS 6:

```
# service temboard reload
```

On RHEL / CentOS 7:

```
# systemctl reload temboard
```

### Stop

On RHEL / CentOS 6:

```
# service temboard stop
```

On RHEL / CentOS 7:

```
# systemctl stop temboard
```

