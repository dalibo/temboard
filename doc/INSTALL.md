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
$ cd temboard-ui/
$ sudo python setup.py install
```

## Prepare directories and files

Creation of directories for the configuration file and SSL files:
```
$ sudo mkdir /etc/temboard-ui
$ sudo mkdir /etc/temboard-ui/ssl
```

Logging directory:
```
$ sudo mkdir /var/log/temboard-ui
```

Copy the sample configuration file:
```
$ sudo cp /usr/share/temboard-ui/temboard-ui.conf.sample /etc/temboard-ui/temboard-ui.conf
```

Copy dummies self-signed SSL key and cacerts files:
```
$ sudo cp /usr/share/temboard-ui/temboard-ui_* /etc/temboard-ui/ssl/.
```

## Users

```
sudo useradd -M -r temboard
```

```
sudo chown -R temboard.temboard /etc/temboard-ui/
sudo chown -R temboard.temboard /var/log/temboard-ui/
sudo chmod 600 /etc//ssl/*
sudo chmod 600 /etc/temboard-ui/temboard-ui.conf
```

## Repository

Repository is a PostgreSQL (>=9.5) database. It requires `tablefunc` extension.

### Configuration

`work_mem` parameter should be set to `16MB`

### Setup

```
sudo -u postgres createuser temboard -l -P
sudo -u postgres createdb -O temboard temboard
psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard-ui/application.sql temboard
sudo -u postgres psql -U postgres -c "CREATE EXTENSION tablefunc" temboard
psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard-ui/supervision.sql temboard
```
