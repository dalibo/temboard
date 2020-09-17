#!/bin/bash -eu
#
# auto_configure.sh setup a Postgres database and temboard UI service.
#
# Run auto_configure.sh as root. You configure it like any libpq software. By
# default, the script access the running cluster on port 5432, using postgres
# UNIX and PostgreSQL user.

ETCDIR=${ETCDIR-/etc/temboard}
VARDIR=${VARDIR-/var/lib/temboard}
LOGDIR=${LOGDIR-/var/log/temboard}
LOGFILE=${LOGFILE-/var/log/temboard-auto-configure.log}


catchall() {
	local rc=$?
	set +x
	if [ $rc -gt 0 ] ; then
		fatal "Failure. See ${LOGFILE} for details."
	else
		rm -f ${LOGFILE}
	fi
	exec 3>&-
	trap - INT EXIT TERM
}


fatal() {
	echo -e "\e[1;31m$@\e[0m" | tee -a /dev/fd/3 >&2
	exit 1
}


log() {
	echo "$@" | tee -a /dev/fd/3 >&2
}


setup_logging() {
	if [ -n "${DEBUG-}" ] ; then
		exec 3>/dev/null
	else
		exec 3>&2 2>${LOGFILE} 1>&2
		chmod 0600 ${LOGFILE}
		trap 'catchall' INT EXIT TERM
	fi

	# Now, log everything.
	set -x
}


setup_pq() {
	# Ensure used libpq vars are defined for configuration template.

	export PGHOST=${PGHOST-$(query_pgsettings unix_socket_directories)}
	PGHOST=${PGHOST%%,*}
	export PGPORT=${PGPORT-5432}
	export PGUSER=${PGUSER-postgres}
	if [ -d ${PGHOST-/tmp} ] ; then
		sudo="sudo -Eu ${PGUSER}"
	else
		sudo=
	fi
	if ! $sudo psql -tc "SELECT 'Postgres connection working.';" ; then
		fatal "Can't connect to Postgres cluster."
	fi
}


setup_ssl() {
	local pki;
	for d in /etc/pki/tls /etc/ssl /etc/temboard; do
		if [ -d $d ] ; then
			pki=$d
			break
		fi
	done
	if [ -z "${pki-}" ] ; then
		fatal "Failed to find PKI directory."
	fi

	if [ -f $pki/certs/ssl-cert-snakeoil.pem -a -f $pki/private/ssl-cert-snakeoil.key ] ; then
		log "Using snake-oil SSL certificate."
		sslcert=$pki/certs/ssl-cert-snakeoil.pem
		sslkey=$pki/private/ssl-cert-snakeoil.key
	else
	     sslcert=$pki/certs/temboard.pem
	     sslkey=$pki/private/temboard.key
	     if ! [ -f $sslcert ] ; then
		     log "Generating self-signed certificate."
		     openssl req -new -x509 -days 365 -nodes \
			     -subj "/C=XX/ST= /L=Default/O=Default/OU= /CN= " \
			     -out $sslcert -keyout $sslkey
	     fi
	fi
	echo $sslcert $sslkey
}


generate_configuration() {
	local sslcert=$1; shift
	local sslkey=$1; shift
	local cookiesecret="$(pwgen 128)"

	cat <<-EOF
	# Configuration initiated by $0 on $(date)
	#
	# See https://temboard.rtfd.io/ for details on configuration
	# possibilities.

	[temboard]
	ssl_cert_file = $sslcert
	ssl_key_file = $sslkey
	cookie_secret = ${cookiesecret}
	home = ${VARDIR}

	[repository]
	host = ${PGHOST}
	port = ${PGPORT}
	user = temboard
	password = ${TEMBOARD_PASSWORD}
	dbname = temboard

	[logging]
	method = stderr
	level = INFO

	[monitoring]
	# purge_after = 365

	[statements]
	# purge_after = 7

	EOF
}

pwgen() {
	# Generates a random password of 32 hexadecimal characters.
	od -vN $((${1-32} / 2)) -An -tx1 /dev/urandom | tr -d ' \n'
}


#       M A I N

cd $(readlink -m ${BASH_SOURCE[0]}/..)

setup_logging
setup_pq

export TEMBOARD_PASSWORD=${TEMBOARD_PASSWORD-$(pwgen)}
if ! getent passwd temboard ; then
	log "Creating system user temBoard."
	useradd \
		--system --user-group --shell /sbin/nologin \
		--home-dir ${VARDIR} \
		--comment "temBoard Web UI" temboard &>/dev/null
fi

if getent group ssl-cert &>/dev/null; then
	adduser temboard ssl-cert
fi


log "Configuring temboard in ${ETCDIR}."
sslfiles=($(set -eu; setup_ssl))
install -o temboard -g temboard -m 0750 -d ${ETCDIR} ${LOGDIR} ${VARDIR}
install -o temboard -g temboard -m 0640 /dev/null ${ETCDIR}/temboard.conf
generate_configuration "${sslfiles[@]}" > ${ETCDIR}/temboard.conf

log "Creating Postgres user, database and schema."
if [ -d ${PGHOST-/tmp} ] ; then
	# If local, sudo to PGUSER.
	sudo -Eu ${PGUSER} ./create_repository.sh
else
	./create_repository.sh
fi
dsn="postgres://temboard:${TEMBOARD_PASSWORD}@/temboard"
if ! sudo -Eu temboard psql -Atc "SELECT 'CONNECTED';" "$dsn" | grep -q 'CONNECTED' ; then
	fatal "Can't configure access to Postgres database."
fi

if hash systemctl &>/dev/null; then
	start_cmd="systemctl start temboard"
	if systemctl is-system-running &>/dev/null ; then
		systemctl daemon-reload
		systemctl enable temboard
	fi
else
	start_cmd="temboard -c ${ETCDIR}/temboard.conf"
fi

log
log "Success. You can now start temboard using:"
log
log "    ${start_cmd}"
log
log "Remember to replace default admin user!!!"
log
