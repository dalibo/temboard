<h1>Installation</h1>

temBoard is designed with three distinct components:

- **repository** - a Postgres database to store users, instances list and
 monitoring data.
- **UI** - the main web interface.
- **agent** - a standalone daemon attached to a single Postgres cluster to manage.


The following diagram illustrates the global architecture of temBoard.

![temBoard architecture](sc/architecture.png)

This document guides you to quickly setup all these components together.


# Prerequisites

temBoard UI requires:

- Python 2.7
- openssl
- bash, sudo and psql for setup script.


# Prepare repository

Before installing temBoard UI, ensure you have a running PostgreSQL 9.5+
cluster. The auto-configuration script works well with a local Postgres cluster,
running as UNIX user `postgres`. If it's not the case, post-inst script will
fail gracefully and let you handle the configuration later.

!!! note

    To ensure browsing of the web interface is fast enough, please note `work_mem`
    parameter PostgreSQL cluster hosting the repository should be set to at least
    `16MB`.

A simple way to check if auto configuration should work is to run:

``` console
# sudo -u postgres psql
```

If this fails, don't worry. You will have to run auto-configuration script with
proper parameters, once temBoard package is installed.


# Installation

Choose the method matching your target system:

<ul class="tabs">
  <li><a href="#debian"><img src="../sc/debian.svg" height="48" width="48"></img> Debian</a></li>
  <li><a href="#rhel-centos"><img src="../sc/centos.svg" height="48" width="48"></img> RHEL / CentOS</a></li>
  <li><a href="#pypi"><img src="../sc/pypi.svg" height="48" width="48"></img> PyPI</a></li>
</ul>

<div id="debian" markdown=1>
<h3>Debian</h3>

temBoard debs are published on [Dalibo Labs APT repository](https://apt.dalibo.org/labs/).
temBoard supports Debian *stretch* and *jessie*. Start by enabling
Dalibo Labs APT repository.


``` console
# echo deb http://apt.dalibo.org/labs $(lsb_release -cs)-dalibo main > /etc/apt/sources.list.d/dalibo-labs.list
# curl https://apt.dalibo.org/labs/debian-dalibo.asc | apt-key add -
# apt update -y
```

You can now install temBoard with:

``` console
# apt install temboard
# temboard --version
```
</div>


<div id="rhel-centos" markdown=1>
<h3>RHEL / CentOS</h3>

temBoard RPM are published on [Dalibo Labs YUM repository](https://yum.dalibo.org/labs/).
temBoard supports RHEL / CentOS 7. Start by enabling Dalibo Labs YUM repository.

``` console
$ sudo yum install -y https://yum.dalibo.org/labs/dalibo-labs-2-1.noarch.rpm
$ sudo yum makecache fast
```

!!! warning

    Do **NOT** use temBoard rpm from PGDG. They are known to be broken.


With the YUM repository configured, you can install temBoard UI with:

``` console
$ sudo yum install temboard
$ temboard --version
```
</div>


<div id="pypi" markdown=1>
<h3>PyPI</h3>

temBoard UI wheel and source tarball are published on
[PyPI](https://pypi.org/project/temboard). Installing from PyPI requires
Python2.7, pip and wheel. It's better to have a recent version of pip.

``` console
$ sudo pip install temboard
$ temboard --version
```

!!! note "temBoard installation prefix"

    temBoard installation prefix may differ from one system to another, e.g. `/usr`
    or `/usr/local`. Please adapt the documentation to match this system prefix.

Now run manually the auto configuration script:

``` console
$ sudo /usr/local/share/temboard/auto_configure.sh
```
</div>


# Post installation

If postinst auto-configuration fails, you can still relaunch it with proper
parameters. Call the script `/usr/share/temboard/auto_configure.sh` with
libpq-style envvars.

The postinst script creates Postgres role, database and tables, as
well as self-signed SSL certificate, UNIX user, configuration file and systemd
unit. A few steps are left to the administrator.

!!! danger "Default admin user"

    By default, temBoard is set up with a dumb `admin` user with password `admin`. This
    is totally unsecured. It is **strongly recommended to change default password**! See below.

First, start temboard using `systemctl start temboard`. Then log in as
`admin:admin` and change the password.

!!! note "Using firewall"
    To increase security, you may protect temBoard using
    a firewall rule, until the quickstart admin is secured.


# Install agents

Once the UI is up and running, you can proceed to agent installation and setup
on each host you want to manage. See dedicated [agent
installation](http://temboard-agent.readthedocs.io/en/v2/installation.html)
documentation for this.

Then, when all instances show up in temBoard, go further with the [How
to](temboard-howto.md).


<script src="../sc/tabs.js" defer="defer"></script>
<style type="text/css">
.tabs {
  text-align: center;
  margin: 0;
  padding: 0;
  display: flex;
  flex-flow: row nowrap;
  justify-content: center;
  align-items: flex-start;
}

.rst-content .section ul.tabs li {
  display: block;
  flex-grow: 1;
  margin: 0;
  padding: 4px;
}

.tabs li + li {
  border-left: 1px solid black;
}

.tabs li img {
  margin: 8px auto;
  display: block;
}

.tabs li a {
  display: inline-block;
  width: 100%;
  padding: 4px;
  font-size: 110%;
}

.tabs li a.active {
  font-weight: bold;
  /* Match RTD bg of current entry in side bar. */
  background: #e3e3e3;
}
</style>
