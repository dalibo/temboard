FROM python:2.7-slim

MAINTAINER Étienne BERSAC <etienne.bersac@dalibo.com>

RUN apt-get update -y \
    # For docker client \
    && apt-get install -y --no-install-recommends libltdl7 postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    ;

RUN useradd --home-dir /var/lib/temboard --create-home --system temboard
VOLUME /var/lib/temboard
WORKDIR /var/lib/temboard

RUN mkdir -p /etc/temboard-agent/ \
&& chown -R temboard. /etc/temboard-agent
VOLUME /etc/temboard-agent

RUN python -c 'import urllib; urllib.urlretrieve("https://github.com/tianon/gosu/releases/download/1.10/gosu-amd64", "/usr/local/bin/gosu")' \
    && chmod 0755 /usr/local/bin/gosu \
    && python -c 'import urllib; urllib.urlretrieve("https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh", "/usr/local/bin/wait-for-it")' \
    && chmod 0755 /usr/local/bin/wait-for-it \
    ;

ENV TEMBOARD_USERS_LIST alice:alice bob:bob
ENV TEMBOARD_SSL_CA /usr/local/share/temboard-agent/temboard-agent_ca_certs_CHANGEME.pem
ENV TEMBOARD_SSL_CERT /usr/local/share/temboard-agent/temboard-agent_CHANGEME.pem
ENV TEMBOARD_SSL_KEY /usr/local/share/temboard-agent/temboard-agent_CHANGEME.key
ENV TEMBOARD_UI_URL ""
ENV TEMBOARD_UI_USER "admin"
ENV TEMBOARD_UI_PASSWORD "admin"
ENV TEMBOARD_GROUPS local_instances

COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["gosu", "temboard", "docker-entrypoint.sh"]
CMD ["temboard-agent"]

RUN pip install --no-cache-dir https://github.com/dalibo/temboard-agent/archive/master.zip

EXPOSE 2345
