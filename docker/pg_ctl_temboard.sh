#! /bin/bash -eu

PGCONTAINER=$1
COMMAND=$2

case $COMMAND in
	start|stop|restart)
		docker $COMMAND $PGCONTAINER
		;;
	*)
		docker exec $PGCONTAINER su postgres -c "/usr/local/bin/pg_ctl $COMMAND"
		;;
esac
