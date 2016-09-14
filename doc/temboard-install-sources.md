# temBoard installation from sources

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

PID directory:
```
$ sudo mkdir /var/run/temboard
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
sudo chown -R temboard.temboard /var/run/temboard/
sudo chmod 600 /etc/temboard/ssl/*
sudo chmod 600 /etc/temboard/temboard.conf
```

## SSL certificate

### Using provided SSL certificate
`temboard` provides a ready to use self-signed SSL certifcate located in `/usr/share/temboard` directory, if you don't want to use it, you can create a new one with the `openssl` binary.
```
$ sudo cp /usr/share/temboard/temboard_CHANGEME.key /etc/temboard/ssl/.
$ sudo cp /usr/share/temboard/temboard_CHANGEME.pem /etc/temboard/ssl/.
$ sudo chown temboard.temboard /etc/temboard/ssl/*
```

### Build a new self-signed certificate

To build a new SSL certifcate:
```
$ sudo -u temboard openssl req -new -x509 -days 365 -nodes -out /etc/temboard/ssl/localhost.pem -keyout /etc/temboard/ssl/localhost.key
```

Then, `ssl_cert_file` and `ssl_key_file` parameters from `temboard.conf` file need to be set respectively to `/etc/temboard/ssl/localhost.pem` and `/etc/temboard/ssl/localhost.key`.

### CA certificate file

Some plugins must be able to send requests to `temboard-agent` using the HTTPS API. To allow this data flow, the HTTPS client implemented by `temboard` needs to have each agent's SSL certifcate (.pem) stored in its CA certificate file. temBoard embeds a default CA cert. file containing agent's default SSL certificate.

```
$ sudo cp /usr/share/temboard/temboard_ca_certs_CHANGEME.pem /etc/temboard/ssl/ca_certs_localhost.pem
```

`ssl_ca_cert_file` parameter in section `[temboard]` from the configuration file needs to be set to `/etc/temboard/ssl/ca_certs_localhost.pem`.

### Restrictions on SSL files
```
$ sudo chmod 0600 /etc/temboard/ssl/*
```


## Repository

The `repository` is a PostgreSQL (>=9.5) database. Usage of plugin `supervision` requires `tablefunc` extension.

### Configuration

`work_mem` parameter should be set to `16MB`


### Setup

To acces the `repository`, `temboard` needs to have its own user and database. To create them:

```
repository# sudo -u postgres createuser temboard -l -P
repository# sudo -u postgres createdb -O temboard temboard
```

### Authentication with password

The PostgreSQL user `temboard` must be allowed to connect to the repository using password authentication (`md5`). The password of `temboard` user should be set in `temboard` configuration file, under section `[repository]`, parameter `password`.

### Installation

`temboard` SQL schema must be loaded:
```
repository# psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard/application.sql temboard
```

If you plan to use the plugin `supervision`:
```
repository# sudo -u postgres psql -U postgres -c "CREATE EXTENSION tablefunc" temboard
repository# psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard/supervision.sql temboard
```

## Operating `temboard`

### Start
```
$ sudo -u temboard temboard -d -p /var/run/temboard/temboard.pid
```

### Stop
```
$ sudo kill $(cat /var/run/temboard/temboard.pid)
```

### Reload configuration
```
$ sudo kill -HUP $(cat /var/run/temboard/temboard.pid)
```
