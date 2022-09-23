FROM debian:bullseye-slim

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it
RUN set -ex; \
    chmod 0755 /usr/local/bin/wait-for-it; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        docker.io \
        iproute2 \
        libltdl7 \
        postgresql-client \
        sudo \
    ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /usr/share/man/man*/*.7*; \
    :

ARG VERSION
COPY dist/temboard-agent_${VERSION}-0dlb1bullseye1_all.deb /tmp
ADD packaging/docker/sudoers /etc/sudoers.d/temboard-agent
ADD packaging/docker/entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ADD packaging/docker/pg_ctl_temboard.sh /usr/local/bin/pg_ctl_temboard.sh

RUN set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        /tmp/temboard-agent_${VERSION}-0dlb1bullseye1_all.deb \
    ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /usr/share/man/man*/*.7*; \
    temboard-agent --version ; \
    :

VOLUME /etc/temboard-agent
VOLUME /var/lib/temboard-agent
WORKDIR /var/lib/temboard-agent
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["temboard-agent"]
