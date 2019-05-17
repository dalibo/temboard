FROM postgres:11-alpine

ADD docker-dev/init_pgtsq.sh /docker-entrypoint-initdb.d/
RUN apk add wget && \
	wget https://yum.dalibo.org/apk/postgresql_11_pg_track_slow_queries-CURRENT.apk && \
	apk add --allow-untrusted ./postgresql_11_pg_track_slow_queries-CURRENT.apk
