# Ganesh UI installation from sources

## Dependencies

  - `python` &gt; **2.7**
  - `python-dev` &gt; **2.7**
  - `python-setuptools` &ge; **0.6**
  - `python-psycopg2` &ge; **2.6.0**
  - `python-tornado` &ge; **3.2**
  - `python-sqlalchemy` &ge; **0.9.8**

## Installation

Install dependencies with `pip`:
```
sudo pip install tornado
sudo pip install psycopg2
sudo pip install sqlalchemy
```

Proceed with the UI installation:

```
$ cd ganesh-web-client/
$ sudo python setup.py install
```

## Prepare directories and files

Creation of directories for the configuration file and SSL files:
```
$ sudo mkdir /etc/ganesh
$ sudo mkdir /etc/ganesh/ssl
```

Logging directory:
```
$ sudo mkdir /var/log/ganesh
```

Copy the sample configuration file:
```
$ sudo cp /usr/share/ganesh/ganesh.conf.sample /etc/ganesh/ganesh.conf
```

Copy dummies self-signed SSL key and cacerts files:
```
$ sudo cp /usr/share/ganesh/ganesh_* /etc/ganesh/ssl/.
```

## Users

```
sudo useradd -M -r ganesh
```

```
sudo chown -R ganesh.ganesh /etc/ganesh/
sudo chown -R ganesh.ganesh /var/log/ganesh/
sudo chmod 600 /etc/ganesh/ssl/*
sudo chmod 600 /etc/ganesh/ganesh.conf
```

## Repository

Repository is a PostgreSQL (>=9.5) database. It requires `tablefunc` extension.

### Configuration

`work_mem` parameter should be set to `16MB`

### Setup

```
sudo -u postgres createuser ganesh -l -P
sudo -u postgres createdb -O ganesh ganesh
psql -U ganesh -1 -v'ON_ERROR_STOP=on' -f /usr/share/ganesh/application.sql ganesh
sudo -u postgres psql -U postgres -c "CREATE EXTENSION tablefunc" ganesh
psql -U ganesh -1 -v'ON_ERROR_STOP=on' -f /usr/share/ganesh/supervision.sql ganesh
```
