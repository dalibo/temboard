## Quickstart

A `docker-compose.quickstart.yml` file is provided. It's aimed to quickly try temboard with
a few postgres servers.

``` console
wget https://raw.githubusercontent.com/dalibo/temboard/master/docker/docker-compose.yml
docker-compose up
```

After starting the docker-compose image, the UI is available on
https://0.0.0.0:8888/ with `admin` / `admin` credentials.

The agents can be accessed with `alice` / `alice` or `bob` / `bob`.

`docker-compose` will launch:

- a PG 9.4 cluster
- a PG 9.5 cluster
- a PG 9.6 cluster
- a temboard agent for each PG cluster
- a standard PG 9.6 cluster for the UI
- a container for the UI


## Warnings

**DO NOT USE THIS IN PRODUCTION**

temBoard docker images are designed for testing and demo. The SSL certificate is
self-signed and the default passwords are public.

temBoard agent is designed to run on same host as PostgreSQL which is
incompatible with Docker service-minded architecture. Temboard agent images
require access to docker socket to restart PostgreSQL. Which you do not want in
production.

If you want to deploy temBoard in a production environment, take some time to
read <http://temboard.rtd.io>.


## Tips

- If you're already running a PostgreSQL instance on your machine, you might
  encounter conflicts with ports `5433`, `5434` and `5435`. If so remove or edit
  `ports` in `docker-compose.yml`.

- If you run docker on a distant linux server: build a simple SSH tunnel to
  reach the temboard server without exposing it on the internet :

   ```
   ssh -L 8888:localhost:8888 your_server_ip
   ```
