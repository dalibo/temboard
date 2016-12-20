# temBoard installation from debian package (jessie)

## Package repository setup

Add the temboard repository to the configuration of APT:

```
echo 'deb https://packages.temboard.io/apt/ jessie main' > /etc/apt/source.list.d/temboard.list
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

A database in a PostgreSQL 9.5 cluster is required to run temBoard, if you intend to host it on the same machine, add the definition of the repository of the PGPG, by following [their howto](https://wiki.postgresql.org/wiki/Apt).

In a nutshell, the following packages shall be installed, the "contribs" are needed by the `supervision` plugin:

```
sudo apt-get install postgresql-9.5 postgresql-contrib-9.5
```

## Installation

```
sudo apt-get install temboard
```

The database access must be set up otherwise the temboard service will not start. See `doc/temboard-repository-setup.md`.

## Operations

### Important files and directories

- /etc/temboard: stores the `temboard.conf` configuration file and SSL certificates
- /var/log/temboard: stores the logs
- /var/run/temboard: stores the PID file

### Start

```
sudo service temboard start
```

### Status

```
sudo service temboard status

● temboard.service - LSB: Start temboard
   Loaded: loaded (/etc/init.d/temboard)
   Active: active (running) since Thu 2016-08-25 16:18:29 CEST; 16h ago
  Process: 6373 ExecStart=/etc/init.d/temboard start (code=exited, status=0/SUCCESS)
   CGroup: /system.slice/temboard.service
           └─6377 /usr/bin/python /usr/bin/temboard -c /etc/temboard/temboard.conf -d -p /var/run/temboard/temboard.pid

Aug 25 16:18:29 debian-tbd-ui temboard[6373]: Starting: temboard.
```

### Reload configuration

```
sudo service temboard reload
```

### Stop

```
sudo service temboard stop
```

## Package building

To create a new debian package from `temboard` sources, the packages `dpkg-dev`, `debhelper` and `dh-python` have to be installed.
```
sudo apt-get install dpkg-dev debhelper dh-python
```

Then, you need to go in `temboard/debian` directory and execute the script `make_deb.sh`. Once the script executed, the .deb file can be found in `../..` directory.

A source package is also available for Debian Jessie in the packages.temboard.io repository.

