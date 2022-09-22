#! /bin/bash -eu

PGCONTAINER=$1
COMMAND=$2

case $COMMAND in
	start|stop|restart)
		docker $COMMAND $PGCONTAINER
		;;
	*)
		docker exec $PGCONTAINER sh -c "SU_PATH=\$PATH su -m postgres -c \"PATH=\$PATH:\$SU_PATH; pg_ctl $COMMAND\""
		;;
esac
