# Hacking on temboard

Setup quickly a development environment with Docker & Compose.

``` console
$ wget https://raw.githubusercontent.com/dalibo/docker/master/temboard/docker-compose.yml
$ docker-compose up
```

Go to https://127.0.0.0:8888/ to access temboard runing with your code!

By default, temboard is daemonized in temboardui-ui container. When editing the
code, kill first the daemonized temboard and then restart it manually.

``` console
$ docker-compose exec temboardui-ui bash
# pkill temboard
# temboard
```
