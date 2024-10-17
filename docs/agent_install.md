This page document a quick way of installing the agent.
For production system, you may want to use trusted certificate and other enhancement.

## Prerequisites

In order to run temBoard agent, you need:

- Linux as underlying OS.
- PostgreSQL 9.6+, listening on UNIX socket. Check with
  `sudo -u postgres psql`.
- openssl.
- Python 3.6+. Check with `python --version`.
- bash, curl and sudo for setup script.
- A [running temBoard UI](server_install.md).

!!! note

    The temBoard agent must run on the same host as the PostgreSQL instance.
    Running an agent on a remote host is not yet supported.


## Install

=== "RHEL"

    temBoard RPM are published on [Dalibo Labs YUM repository]. temBoard agent supports
    RHEL/CentOS 7 and 8. Start by enabling Dalibo Labs YUM repository.

    ``` console
    $ sudo yum install -y epel-release
    $ sudo yum install -y https://yum.dalibo.org/labs/dalibo-labs-4-1.noarch.rpm
    ```

    !!! Warning

        Do **NOT** use temBoard agent rpm from PGDG. They are known to be
        broken.

    With the YUM repository configured, you can install temBoard agent with:

    ``` console
    $ sudo yum install temboard-agent
    $ temboard-agent --version
    ```

    **Offline install**

    Some production infrastructure are offline for security reasons. In this
    situation, the temboard-agent package and its dependencies can be dowloaded
    with the following commands :

    ``` console
    $ sudo yum install yum-utils
    $ yumdownloader --resolve --destdir /tmp/temboard-packages temboard-agent
    ```

    Then the downloaded packages can be transfered to the production server and
    installed with

    ``` console
    $ yum --disablerepo=* localinstall *.rpm
    ```

=== "Debian"

    temBoard debs are published on [Dalibo Labs APT
    repository](https://apt.dalibo.org/labs/). temBoard agent supports Debian
    buster and newer. Start by enabling Dalibo Labs APT repository.

    ``` console
    # echo deb http://apt.dalibo.org/labs $(lsb_release -cs)-dalibo main > /etc/apt/sources.list.d/dalibo-labs.list
    # curl -fsSL -o /etc/apt/trusted.gpg.d/dalibo-labs.gpg https://apt.dalibo.org/labs/debian-dalibo.gpg
    # apt update  # You may use apt-get here.
    ```

    You can install now temBoard agent with:

    ``` console
    # apt install temboard-agent
    # temboard-agent --version
    ```


=== "PyPI"

    temBoard agent wheel and source tarball are published on
    [PyPI](https://pypi.org/project/temboard-agent).

    Installing from PyPI requires Python3.6+, pip and wheel. It\'s better to
    have a recent version of pip.

    ``` console
    $ sudo pip install temboard-agent
    $ temboard-agent --version
    ```

    Note where is installed temBoard agent and determine the prefix. You
    must find a `share/temboard-agent` folder in e.g `/usr` or `/usr/local`.
    If temBoard agent is installed in `/usr/local`, please adapt the
    documentation to match this system prefix.


## Configure

The quickest way to setup temBoard agent is to use the
`auto_configure.sh` script, installed in `/usr/share/temboard-agent`.

You must run this script as root, with `PG*` env vars set to connect to
the Postgres cluster you want to manage. By default, the script uses
`postgres` UNIX user to connect to Postgres cluster.

!!! Note

    Each instance is identified by the fully qualified *hostname*. If
    `hostname --fqdn` can\'t resolve the FQDN of your HOST, simply overwrite
    it using `TEMBOARD_HOSTNAME` envvar. Remember that `localhost` or even a
    short hostname is not enough. `auto_configure.sh` enforces this.

``` console
# /usr/share/temboard-agent/auto_configure.sh https://temboard.acme.tld:8888
```

The script shows you some important information for the next steps:

- agent TCP port (usually 2345 if this is your first agent on this host).
- the path to the main agent configuration file like
  `/etc/temboard-agent/14/main/temboard-agent.conf`

Next you need to fetch the signing public key of temBoard UI.
An agent accepts requests from a single temBoard UI.
temBoard UI signs each requests using an asymetric key.
Use `temboard-agent fetch-key` to download the signing key from the configured UI.
Or push the signing using a configuration management service.

``` console
# temboard-agent --config /etc/temboard-agent/14/main/temboard-agent.conf fetch-key
```

## Start

Now start the agent using the command suggested by `auto_configure.sh`.
On most systems now, it\'s a systemd service:

``` console
# systemctl enable --now temboard-agent@14-main
```

Check that it has started successfully:

``` console
# systemctl status temboard-agent@14-main
```

!!! Note

    temBoard agent OOM score is configured to 15, so that OOM killer will likely kill temBoard agent before Postgres.
    A good practice is to disable memory overcommit on PostgreSQL host by setting sysctl `vm.overcommit_memory = 2`.

## Register


### Register from the monitored instance

Now you can register the agent in the UI using `temboard-agent register`.
It needs the configuration file path, the agent host and port and the path to the
temBoard UI.:

``` console
# sudo -u postgres temboard-agent -c /etc/temboard-agent/14/main/temboard-agent.conf register --environment default
```

`temboard-agent register` will ask you credentials to the temBoard UI with
admin privileges.

!!! Note

    the `--environment` (or `-e`) option replaces the `--groups` (or `g`) option that
    was used in version 8.

### Register from the UI

Alternatively it is possible to register an instance on the temBoard server.

This can be done either by running the following command line **on the temboard server**:

``` console
# sudo -u temboard temboard register-instance foo.acme.tld -e default --if-not-exists
```

( Replace `foo.acme.tld` by the named of the monitored instance )

Or connect to the web interface, go to the `Settings > Instances` page and click on
the `Add new instance` button.


## It's up!

Congratulation! You can continue on the UI and see the agent appeared,
and monitoring data being graphed.

You can repeat the above setup for each instance on the same host.

## Clean the agent installation

If you need to clean a single agent installation either to uninstall it
or to run `auto_configure.sh` again, use `purge.sh` with cluster name.

``` console
# /usr/share/temboard-agent/purge.sh 12/main
Stopping and disabling systemd service.
Removed /etc/systemd/system/multi-user.target.wants/temboard-agent@12-main.service.
Cleaning files and directories...
removed '/etc/temboard-agent/12/main/temboard-agent.conf'
removed '/etc/temboard-agent/12/main/temboard-agent.conf.d/auto.conf'
removed directory '/etc/temboard-agent/12/main/temboard-agent.conf.d'
removed '/etc/temboard-agent/12/main/users'
removed directory '/etc/temboard-agent/12/main/'
removed directory '/var/lib/temboard-agent/12/main/'
temBoard agent 12-main stopped and cleaned.
#
```

( Replace `12/main` with the version and name of the PostgreSQL monitored instance. )

[Dalibo Labs YUM Repository]: https://yum.dalibo.org/labs/
