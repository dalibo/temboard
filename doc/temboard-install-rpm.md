# temBoard installation from RPM package on RHEL / CentOS 7

## Package repository setup

The following YUM repository are required to install `temboard`:

* [yum.postgresql.org](http://yum.postgresql.org/repopackages.php) for PostgreSQL
* [temBoard package repository](https://packages.temboard.io/yum/) for temBoard

### RHEL / CentOS 7

Install the `packages.temboard.io` repository by creating the `/etc/yum.repos.d/temboard.repo` file with the following contents:

```
[temboard]
name=temBoard Packages for Enterprise Linux 7
baseurl=https://packages.temboard.io/yum/rhel7/
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
