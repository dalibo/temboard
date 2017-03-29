FROM python:2.7-slim

MAINTAINER Étienne BERSAC <etienne.bersac@dalibo.com>

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    ;

RUN pip install --no-cache-dir https://github.com/dalibo/temboard/archive/master.zip
RUN python -c 'import urllib; urllib.urlretrieve("https://github.com/tianon/gosu/releases/download/1.10/gosu-amd64", "/usr/local/bin/gosu")' \
    && chmod 0755 /usr/local/bin/gosu \
    && python -c 'import urllib; urllib.urlretrieve("https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh", "/usr/local/bin/wait-for-it")' \
    && chmod 0755 /usr/local/bin/wait-for-it \
    ;

ENV TEMBOARD_COOKIE_SECRET SECRETKEYTOBECHANGED
ENV TEMBOARD_SSL_CA /usr/local/share/temboard/temboard_ca_certs_CHANGEME.pem
ENV TEMBOARD_SSL_CERT /usr/local/share/temboard/temboard_CHANGEME.pem
ENV TEMBOARD_SSL_KEY /usr/local/share/temboard/temboard_CHANGEME.key

RUN useradd --home-dir /var/lib/temboard --create-home --system temboard
VOLUME /var/lib/temboard
WORKDIR /var/lib/temboard

COPY fixture.sql /var/lib/temboard/
COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["gosu", "temboard", "docker-entrypoint.sh"]
CMD ["temboard --config temboard.conf"]

EXPOSE 8888
