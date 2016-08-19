# Temboard UI installation from sources

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

Proceed with the installation of the UI:

```
$ cd temboard/
$ sudo python setup.py install
```

## Prepare directories and files

Creation of directories for the configuration file and SSL files:
```
$ sudo mkdir /etc/temboard
$ sudo mkdir /etc/temboard/ssl
```

Logging directory:
```
$ sudo mkdir /var/log/temboard
```

Copy the sample configuration file:
```
$ sudo cp /usr/share/temboard/temboard.conf.sample /etc/temboard/temboard.conf
```

Copy dummies self-signed SSL key and cacerts files:
```
$ sudo cp /usr/share/temboard/temboard_* /etc/temboard/ssl/.
```

## Users

```
sudo useradd -M -r temboard
```

```
sudo chown -R temboard.temboard /etc/temboard/
sudo chown -R temboard.temboard /var/log/temboard/
sudo chmod 600 /etc//ssl/*
sudo chmod 600 /etc/temboard/temboard.conf
```

## Repository

Repository is a PostgreSQL (>=9.5) database. It requires `tablefunc` extension.

### Configuration

`work_mem` parameter should be set to `16MB`

### Setup

```
sudo -u postgres createuser temboard -l -P
sudo -u postgres createdb -O temboard temboard
psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard/application.sql temboard
sudo -u postgres psql -U postgres -c "CREATE EXTENSION tablefunc" temboard
psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard/supervision.sql temboard
```
