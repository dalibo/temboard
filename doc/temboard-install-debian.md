# Temboard installation from debian package (jessie)

## Package building

To create a new debian package from `temboard` sources, the packages `dpkg-dev`, `debhelper` and `dh-python` have to be installed.
```
$ sudo apt-get install dpkg-dev debhelper dh-python
```

Then, you need to go in `temboard/debian` directory and execute the script `make_deb.sh`. Once the script executed, the .deb file can be found in `../..` directory.

## Installation

```
$ sudo apt-get install python-pycurl python-tornado python-sqlalchemy python-psycopg2
$ sudo dpkg -i temboard_0.0.1-6_all.deb
```

## Operations

### Start

```
$ sudo service temboard start
```

### Status

```
$ sudo service temboard status

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
$ sudo service temboard reload
```

### Stop

```
$ sudo service temboard stop
```
